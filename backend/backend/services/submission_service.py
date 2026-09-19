"""Immutable attempts, explicit artifact serialization and release filtering."""
from pathlib import Path
from sqlalchemy import select
from backend.models.file import File
from backend.models.submissions import Submission
from backend.models.teaching import GradingGuidance
from backend.models.enums import SubmissionStatus, UserRole
from backend.repository.task_repository import _get_task
from backend.repository.file_repository import get_file_by_id
from backend.repository.submission_repository import (
    get_next_attempt_number, mark_previous_submissions_not_latest,
    get_student_submissions as history, get_submission,
)
from backend.repository.rubric_repository import get_accepted_rubric
from backend.schemas.submission import SubmissionDetailResponse, SubmissionListItemResponse
from backend.services.access import check_task_access, eligibility, fail, lock_attempts, student_user
from backend.services.team_service import lock_rosters, submission_team, complete_roster, now

async def create_submission(task_id, student_id, db, submission_text="", file_id=None, team_id=None,repository_snapshot_id=None):
    task = await _get_task(task_id, db)
    user = await student_user(student_id, db)
    check_task_access(task, user)
    team_required = task.project_details and task.project_details.require_team
    if team_required:
        await lock_rosters(task_id, db)
    await lock_attempts(db, task_id, student_id, wait=False)
    access = await eligibility(task, user, db)
    if not access["allowed"]:
        fail(access["reason_code"], "Submission is unavailable: " + access["reason_code"])
    team = None
    if team_required:
        team, reason = await submission_team(task, user, db)
        if reason:
            fail(reason, "An approved team is required.")
        if team_id is not None and team.id != team_id:
            fail("team_forbidden", "This is not your approved team.", 403)
        await complete_roster(team, user, db)
    elif team_id is not None:
        fail("team_not_required", "Individual tasks do not accept a team ID.", 422)
    snapshot=None
    if repository_snapshot_id is not None:
        if file_id is not None:
            fail("repository_artifact_conflict","Choose a file OR a repository snapshot.",422)
        from backend.services.repository_service import attach
        snapshot=await attach(repository_snapshot_id,team,user,db)
    if not submission_text.strip() and file_id is None and snapshot is None:
        fail("empty_submission", "Include text or an uploaded file.", 422)
    file = None
    if file_id is not None:
        file = await db.scalar(select(File).where(File.id == file_id).with_for_update().execution_options(populate_existing=True))
        if not file:
            fail("file_not_found", "File not found.", 404)
        if file.owner_id != student_id or file.purpose != "submission":
            fail("file_forbidden", "This is not your submission file.", 403)
        if file.task_id not in (None, task_id):
            fail("file_task_mismatch", "File belongs to another task.", 422)
        if file.submission_id is not None:
            fail("file_already_submitted", "This file belongs to an earlier attempt; upload a new copy.")
        if task.assignment_details and file.file_type not in task.assignment_details.allowed_file_types:
            fail("file_type_not_allowed", "This file type is not allowed for the assignment.", 422)
    rubric = await get_accepted_rubric(task_id, db)
    attempt = await get_next_attempt_number(task_id, student_id, db)
    await mark_previous_submissions_not_latest(task_id, student_id, db)
    submission = Submission(task_id=task_id, student_id=student_id, rubric_id=rubric.id,
        repository_snapshot_id=snapshot.id if snapshot else None,
        team_id=team.id if team else None, team_snapshot=team.approved_roster if team else None,
        submission_text=submission_text, attempt_number=attempt, is_latest=True,
        total_possible_grade=sum(c.max_points for c in rubric.criteria), status=SubmissionStatus.pending)
    db.add(submission)
    await db.flush()
    if team:
        team.locked_at = team.locked_at or now()
    if file:
        file.submission_id, file.task_id = submission.id, task_id
    await db.commit()
    return submission

def summary(submission, student=False):
    data = SubmissionListItemResponse.model_validate(submission)
    if student and submission.status != SubmissionStatus.staff_confirmed:
        data.ai_suggested_grade = data.final_grade = data.feedback = None
    return data

async def get_student_submissions(task_id, student_id, db):
    task = await _get_task(task_id, db)
    check_task_access(task, await student_user(student_id, db))
    return [summary(s, student=True) for s in await history(task_id, student_id, db)]

async def get_submission_details(submission_id, current_user, db):
    submission = await get_submission(submission_id, db)
    student = current_user.role == UserRole.student
    if student and submission.student_id != current_user.id:
        fail("submission_forbidden", "You can only view your own submissions.", 403)
    if student:
        check_task_access(await _get_task(submission.task_id, db), current_user)
    visible = not student or submission.status == SubmissionStatus.staff_confirmed
    data = {key: getattr(submission, key) for key in (
        "id", "task_id", "student_id", "team_id", "submission_text", "attempt_number",
        "is_latest", "status", "submitted_at", "rubric_id", "team_snapshot")}
    data.update(rubric_version=submission.rubric.version,
        total_possible_grade=sum(c.max_points for c in submission.rubric.criteria),
        file_id=submission.files[0].id if submission.files else None,
        artifacts=[{"file_id": f.id, "file_name": f.original_filename or Path(f.storage_path).name,
                    "file_type": f.file_type} for f in submission.files],
        rubric_criteria=[{"name": c.name, "description": c.description, "max_points": c.max_points,
                          "sort_order": c.sort_order}
                         for c in sorted(submission.rubric.criteria, key=lambda c: c.sort_order)])
    for key in ("ai_suggested_grade", "final_grade", "feedback", "confirmed_by", "confirmed_at",
                "criterion_evaluations", "ai_warnings", "is_mock"):
        data[key] = getattr(submission, key) if visible else None
    data["code_reviews"] = [{"file_path": r.file_path, "line_number": r.line_number,
        "severity": r.severity.value, "finding": r.finding} for r in submission.code_reviews] if visible else None
    if current_user.role in (UserRole.professor, UserRole.teaching_assistant) and submission.grading_guidance_id:
        guidance = await db.get(GradingGuidance, submission.grading_guidance_id)
        data["grading_guidance_id"] = guidance.id if guidance else None
        data["grading_guidance_version"] = guidance.version if guidance else None
    if submission.repository_snapshot_id:
        from backend.models.repository import RepositorySnapshot
        from backend.schemas.repository import SnapshotInfo
        data["repository_snapshot"]=SnapshotInfo.model_validate(await db.get(RepositorySnapshot,submission.repository_snapshot_id))
    return SubmissionDetailResponse(**data)
