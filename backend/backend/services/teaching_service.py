"""Staff-only teaching tools. Never send work, identities or feedback to analytics."""
import asyncio
import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from pydantic import ValidationError
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from ai_tutor.config import Config
from ai_tutor.models import CohortAnalyticsRequest, CohortGradeSnapshot, CohortCriterionSnapshot, CohortCodeReviewSnapshot
from backend.core.ai import ai
from backend.models.enums import SubmissionStatus
from backend.models.rubric import Rubric
from backend.models.submissions import Submission
from backend.models.teaching import GradingGuidance, TeachingReport
from backend.repository.task_repository import _get_task
from backend.schemas.teaching import (
    GuidanceInfo, GuidanceList, CriterionStatistic, RubricGroup, TaskAnalytics,
    TeachingSuggestions, TeachingReportInfo, TeachingReportList,
)
from backend.services.access import fail
from backend.services.ai_service import call_ai
from backend.services.exceptions import AIRubricError

MINIMUM = max(3, Config.MIN_COHORT_SIZE_FOR_PATTERNS)
TIMEOUT = max(1, min(int(os.getenv("ANALYTICS_TIMEOUT_SECONDS", "90")), 120))


async def latest_guidance(task_id, db):
    return await db.scalar(select(GradingGuidance).where(GradingGuidance.task_id == task_id)
                           .order_by(GradingGuidance.version.desc()).limit(1))


async def create_guidance(task_id, body, user, db):
    await _get_task(task_id, db)
    await db.execute(text("SELECT pg_advisory_xact_lock(:task, -775)"), {"task": task_id})
    previous = await db.scalar(select(GradingGuidance).where(GradingGuidance.task_id == task_id,
                                                          GradingGuidance.request_id == str(body.request_id)))
    if previous:
        if previous.content != body.content or previous.created_by != user.id:
            fail("request_conflict", "Request ID was already used.")
        return GuidanceInfo.model_validate(previous)
    latest = await latest_guidance(task_id, db)
    row = GradingGuidance(task_id=task_id, version=latest.version + 1 if latest else 1,
        content=body.content, request_id=str(body.request_id), created_by=user.id)
    db.add(row)
    await db.commit()
    return GuidanceInfo.model_validate(row)


async def guidance_detail(task_id, guidance_id, db):
    await _get_task(task_id, db)
    row = await db.get(GradingGuidance, guidance_id)
    if not row or row.task_id != task_id:
        fail("not_found", "Guidance version not found.", 404)
    return GuidanceInfo.model_validate(row)


async def list_guidance(task_id, db, before, limit):
    await _get_task(task_id, db)
    query = select(GradingGuidance).where(GradingGuidance.task_id == task_id)
    if before:
        query = query.where(GradingGuidance.id < before)
    rows = list((await db.scalars(query.order_by(GradingGuidance.id.desc()).limit(limit + 1))).all())
    return GuidanceList(items=[GuidanceInfo.model_validate(r) for r in rows[:limit]],
        next_cursor=rows[limit-1].id if len(rows) > limit else None)


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


async def analytics_snapshot(task_id, db):
    task = await _get_task(task_id, db)
    # Rank confirmed rows, NOT all attempts: historical data may have a newer unconfirmed attempt.
    ranked = select(Submission.id, func.row_number().over(partition_by=Submission.student_id,
        order_by=(Submission.attempt_number.desc(), Submission.id.desc())).label("position")).where(
        Submission.task_id == task_id, Submission.status == SubmissionStatus.staff_confirmed).subquery()
    rows = list((await db.scalars(select(Submission).join(ranked, ranked.c.id == Submission.id)
        .where(ranked.c.position == 1).order_by(Submission.id)
        .options(selectinload(Submission.rubric).selectinload(Rubric.criteria),
                 selectinload(Submission.code_reviews)).execution_options(populate_existing=True).limit(10001))).all())
    if len(rows) > 10000:
        fail("analytics_limit", "This task exceeds the interactive analysis limit.", 422)
    groups, raw_groups, fingerprint_rows = [], defaultdict(list), []
    excluded = 0
    for row in rows:
        total = sum(c.max_points for c in row.rubric.criteria)
        if not valid_number(total) or total <= 0 or not valid_number(row.final_grade) or not 0 <= row.final_grade <= total:
            excluded += 1
            continue
        raw_groups[row.rubric_id].append((row, total))
        # Only the hash is exposed. Student identities, free text and artifact names are not hashed inputs.
        fingerprint_rows.append(dict(id=row.id, confirmed_at=str(row.confirmed_at), grade=row.final_grade,
            rubric=row.rubric_id, total=total, mock=row.is_mock,
            criteria=[{k: c.get(k) for k in ("criterion_name", "score_given", "max_points")}
                      for c in (row.criterion_evaluations or [])],
            severities=sorted(r.severity.value for r in row.code_reviews)))
    fingerprint = hashlib.sha256(json.dumps({"rows": fingerprint_rows, "minimum": MINIMUM},
        sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
    for rubric_id, members in raw_groups.items():
        rubric = members[0][0].rubric
        eligible = len(members) >= MINIMUM
        percentages = [s.final_grade / total * 100 for s, total in members]
        criteria = []
        ordered = sorted(rubric.criteria, key=lambda c: (c.sort_order, c.id))
        name_counts = Counter(c.name for c in ordered)
        for index, criterion in enumerate(ordered, 1):
            scores = []
            for row, _ in members:
                matches = [c for c in (row.criterion_evaluations or []) if c.get("criterion_name") == criterion.name]
                if name_counts[criterion.name] != 1 or len(matches) != 1:
                    continue  # Never guess ambiguous/absent historical criterion associations.
                value = matches[0]
                score = value.get("score_given")
                if (valid_number(score) and 0 <= score <= criterion.max_points
                        and value.get("max_points") == criterion.max_points):
                    scores.append(score)
            enough = eligible and len(scores) >= MINIMUM
            criteria.append(CriterionStatistic(criterion_id=criterion.id, name=criterion.name,
                label=f"Criterion {index}", max_points=criterion.max_points, sample_count=len(scores),
                average_score=round(sum(scores)/len(scores), 4) if enough else None,
                low_score_count=sum(s < criterion.max_points * 0.6 for s in scores) if enough else None))
        severity = Counter(r.severity.value for row, _ in members for r in row.code_reviews)
        groups.append(RubricGroup(rubric_id=rubric_id, rubric_version=rubric.version,
            student_count=len(members), eligible=eligible,
            average_percentage=round(sum(percentages)/len(percentages), 2) if eligible else None,
            minimum_percentage=round(min(percentages), 2) if eligible else None,
            maximum_percentage=round(max(percentages), 2) if eligible else None,
            below_half_count=sum(p < 50 for p in percentages) if eligible else None,
            criteria=criteria, severity_counts=dict(severity) if eligible else None,
            mock_assessment_count=sum(row.is_mock is True for row, _ in members),
            unknown_provenance_count=sum(row.is_mock is None for row, _ in members)))
    return task, TaskAnalytics(task_id=task_id, minimum_group_size=MINIMUM,
        released_count=sum(g.student_count for g in groups), excluded_count=excluded,
        input_fingerprint=fingerprint, groups=sorted(groups, key=lambda g: g.rubric_version)), raw_groups


def report_info(row, fingerprint):
    return TeachingReportInfo(**{key: getattr(row, key) for key in (
        "id", "task_id", "rubric_id", "rubric_version", "language", "input_fingerprint",
        "input_snapshot", "result", "is_mock", "ai_metadata", "created_at")},
        stale=row.input_fingerprint != fingerprint)


async def list_reports(task_id, db, before, limit):
    _, snapshot, _ = await analytics_snapshot(task_id, db)
    query = select(TeachingReport).where(TeachingReport.task_id == task_id)
    if before:
        query = query.where(TeachingReport.id < before)
    rows = list((await db.scalars(query.order_by(TeachingReport.id.desc()).limit(limit + 1))).all())
    return TeachingReportList(items=[report_info(r, snapshot.input_fingerprint) for r in rows[:limit]],
        next_cursor=rows[limit-1].id if len(rows) > limit else None)


async def generate_report(task_id, body, user, db):
    await _get_task(task_id, db)
    acquired = await db.scalar(text("SELECT pg_try_advisory_xact_lock(:task, -774)"), {"task": task_id})
    if not acquired:
        fail("analytics_busy", "A teaching report is already being generated. Refresh before retrying.")
    task, snapshot, raw_groups = await analytics_snapshot(task_id, db)
    previous = await db.scalar(select(TeachingReport).where(TeachingReport.task_id == task_id,
                                                           TeachingReport.request_id == str(body.request_id)))
    if previous:
        if (previous.rubric_id, previous.language, previous.created_by) != (body.rubric_id, body.language, user.id):
            fail("request_conflict", "Request ID was already used with different options.")
        return report_info(previous, snapshot.input_fingerprint)
    group = next((g for g in snapshot.groups if g.rubric_id == body.rubric_id), None)
    if not group or not group.eligible:
        fail("analytics_insufficient", "At least the configured minimum of released results is required for this rubric.", 422)
    # Only generated labels and numeric evidence cross this boundary. No authored task/rubric text.
    payload = CohortAnalyticsRequest(task_title="Released task results", task_description="",
        response_language=body.language, task_type=task.type.value,
        rubric_criteria_names=[c.label for c in group.criteria],
        grades=[CohortGradeSnapshot(grade=row.final_grade, max_grade=total) for row, total in raw_groups[body.rubric_id]],
        criterion_stats=[CohortCriterionSnapshot(criterion_name=c.label, average_score=c.average_score,
            max_points=c.max_points, low_score_count=c.low_score_count)
            for c in group.criteria if c.average_score is not None],
        code_reviews=[CohortCodeReviewSnapshot(severity=severity, finding="Aggregate released finding count",
            count=count) for severity, count in (group.severity_counts or {}).items() if count])
    started = time.monotonic()
    try:
        result = await asyncio.wait_for(call_ai(ai.analyze_cohort_patterns, payload), timeout=TIMEOUT)
    except TimeoutError:
        fail("ai_unavailable", "Teaching analysis timed out. Refresh reports before retrying.", 503)
    try:
        suggestions = TeachingSuggestions.model_validate(result.model_dump())
        if not suggestions.summary.strip() or len(suggestions.model_dump_json()) > 40000:
            raise ValueError("Unusable teaching report")
    except (ValidationError, ValueError) as exc:
        raise AIRubricError("Invalid teaching report") from exc
    meta = result.ai_metadata
    metadata = {key: getattr(meta, key, None) for key in ("provider", "model_used", "prompt_version", "ai_engine_version")}
    metadata.update(latency_ms=round((time.monotonic() - started) * 1000, 2),
                    output_sanitized=bool(getattr(meta, "output_sanitized", False)))
    row = TeachingReport(task_id=task_id, rubric_id=group.rubric_id, rubric_version=group.rubric_version,
        request_id=str(body.request_id), language=body.language, input_fingerprint=snapshot.input_fingerprint,
        input_snapshot=group.model_dump(mode="json"), result=suggestions.model_dump(mode="json"),
        is_mock=ai.engine.mock_mode, ai_metadata=metadata, created_by=user.id)
    db.add(row)
    await db.commit()
    # New releases during provider execution do not rewrite this frozen report; mark it stale.
    _, current, _ = await analytics_snapshot(task_id, db)
    return report_info(row, current.input_fingerprint)
