"""Owner-only tutoring. Assessment authorization is enforced before building prompts."""
import asyncio
import datetime as dt
import os
import time
from uuid import uuid4

from sqlalchemy import select, func, text, update, or_
from ai_tutor.models import SocraticChatRequest, LabAssistantChatRequest, ChatMessage as AIMessage
from backend.core.ai import ai
from backend.models.chat import ChatSession, ChatMessage, ChatTurn, ChatShare, TaskTutorSettings
from backend.models.users import User
from backend.models.enums import SenderType, SubmissionStatus, UserRole
from backend.repository.task_repository import _get_task
from backend.repository.submission_repository import get_submission
from backend.repository.rubric_repository import get_accepted_rubric
from backend.repository.embedding_repository import get_reference_text
from backend.schemas.chat import (ChatInfo, ChatList, ChatTurnInfo, ChatTurnList, ShareInfo, ShareDetail,
    ShareList, SharedTurn, TutorSettings, LegacyMessage, LegacyMessages)
from backend.services.access import check_task_access, fail
from backend.services.ai_service import call_ai
from backend.services.exceptions import NoAcceptedRubric, AIServiceError, AIRubricError, AIRequestError

TIMEOUT = max(1, min(int(os.getenv("TUTOR_TIMEOUT_SECONDS", "90")), 120))
RATE = max(1, int(os.getenv("TUTOR_TURNS_PER_MINUTE", "10")))
MAX_RETRIES = 3


def now():
    return dt.datetime.now(dt.timezone.utc)


async def task_for_user(task_id, user, db):
    task = await _get_task(task_id, db)
    check_task_access(task, user)
    return task


async def owned_session(session_id, user, db):
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        fail("not_found", "Conversation not found.", 404)
    if session.task_id is None:
        fail("chat_unavailable", "This legacy conversation has no task context.", 409)
    await task_for_user(session.task_id, user, db)
    return session


async def linked_submission(submission_id, task_id, user, db):
    submission = await get_submission(submission_id, db)
    if submission.student_id != user.id or submission.task_id != task_id:
        fail("submission_forbidden", "Submission does not belong to you and this task.", 403)
    return submission


async def create_session(task_id, body, user, db):
    task = await task_for_user(task_id, user, db)
    if body.submission_id:
        await linked_submission(body.submission_id, task_id, user, db)
    # Serialize session creation and turn rate accounting per user, not provider execution.
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -772)"), {"user": user.id})
    old = await db.scalar(select(ChatSession).where(ChatSession.user_id == user.id,
        ChatSession.request_id == str(body.request_id)))
    if old:
        if (old.task_id, old.submission_id, old.language) != (task_id, body.submission_id, body.language):
            fail("request_conflict", "Request ID was already used for a different conversation.")
        return ChatInfo.model_validate(old)
    session = ChatSession(user_id=user.id, task_id=task_id, submission_id=body.submission_id,
        request_id=str(body.request_id), language=body.language, title=task.title[:255])
    db.add(session)
    await db.commit()
    return ChatInfo.model_validate(session)


async def list_sessions(task_id, user, db, before, limit):
    await task_for_user(task_id, user, db)
    query = select(ChatSession).where(ChatSession.task_id == task_id, ChatSession.user_id == user.id)
    if before:
        query = query.where(ChatSession.id < before)
    rows = list((await db.scalars(query.order_by(ChatSession.id.desc()).limit(limit + 1))).all())
    return ChatList(items=[ChatInfo.model_validate(s) for s in rows[:limit]],
                    next_cursor=rows[limit - 1].id if len(rows) > limit else None)


async def turn_info(turn, db):
    message = await db.get(ChatMessage, turn.user_message_id)
    reply = await db.get(ChatMessage, turn.assistant_message_id) if turn.assistant_message_id else None
    expired = turn.status == "pending" and turn.lease_until <= now()
    state = "failed" if expired else turn.status
    return ChatTurnInfo(id=turn.id, request_id=turn.request_id, content=message.content,
        reply=reply.content if reply else None, status=state,
        error_code="chat_interrupted" if expired else turn.error_code,
        retryable=state == "failed" and turn.attempt_count < MAX_RETRIES,
        is_mock=turn.is_mock, context_info=turn.context_info, ai_metadata=turn.ai_metadata, created_at=message.created_at)


async def list_turns(session_id, user, db, before, limit):
    await owned_session(session_id, user, db)
    query = select(ChatTurn).where(ChatTurn.session_id == session_id)
    if before:
        query = query.where(ChatTurn.id < before)
    rows = list((await db.scalars(query.order_by(ChatTurn.id.desc()).limit(limit + 1))).all())
    return ChatTurnList(items=[await turn_info(row, db) for row in reversed(rows[:limit])],
                        next_cursor=rows[limit - 1].id if len(rows) > limit else None)


async def build_context(session, user, db):
    task = await task_for_user(session.task_id, user, db)
    info = dict(task_id=task.id, reference_file_id=None, rubric_version=None,
                submission_id=session.submission_id, released_feedback=False, truncated=False)
    settings = await db.get(TaskTutorSettings, task.id)
    if task.type.value == "lab":
        info["lab_mode"] = settings.lab_mode if settings else "experiment"
    sections = []
    def add(label, value, budget):
        if value:
            info["truncated"] |= len(value) > budget
            sections.append(f"{label}:\n{value[:budget]}")
    add("Public task instructions", task.description, 4000)
    reference = await get_reference_text(task.id, db)
    if reference:
        add("Public task reference", reference, 4000)
        info["reference_file_id"] = task.reference_file_id
    submission = await linked_submission(session.submission_id, task.id, user, db) if session.submission_id else None
    rubric = submission.rubric if submission else None
    if not rubric:
        try:
            rubric = await get_accepted_rubric(task.id, db)
        except NoAcceptedRubric:
            pass
    if rubric:
        add("Approved grading expectations", "\n".join(
            f"{c.name} ({c.max_points}): {c.description or ''}" for c in rubric.criteria), 2000)
        info["rubric_version"] = rubric.version
    if submission:
        add("Student's own submitted explanation", submission.submission_text, 4000)
        # Artifact contents are not implicitly ingested. Students can paste a focused excerpt.
        if submission.status == SubmissionStatus.staff_confirmed:
            add("Released assessment feedback", submission.feedback, 2000)
            info["released_feedback"] = bool(submission.feedback)
    context = "\n\n".join(sections)
    info["truncated"] |= len(context) > 12000
    return task, context[:12000], info


async def send_turn(session_id, body, user, db):
    session = await owned_session(session_id, user, db)
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -772)"), {"user": user.id})
    turn = await db.scalar(select(ChatTurn).where(ChatTurn.session_id == session_id,
                                                 ChatTurn.request_id == str(body.request_id)))
    if turn:
        original = await db.get(ChatMessage, turn.user_message_id)
        if original.content != body.content:
            fail("request_conflict", "Request ID was already used for another message.")
        if turn.status == "completed":
            return await turn_info(turn, db)
        if turn.status == "pending" and turn.lease_until > now():
            fail("chat_busy", "A tutor response is still in progress.")
        if not body.retry:
            return await turn_info(turn, db)
        if turn.attempt_count >= MAX_RETRIES:
            fail("chat_retry_limit", "Start a new message after three failed attempts.", 429)
    elif body.retry:
        fail("not_found", "Turn not found.", 404)
    active = await db.scalar(select(ChatTurn.id).where(ChatTurn.session_id == session_id,
        ChatTurn.status == "pending", ChatTurn.lease_until > now()).limit(1))
    if active:
        fail("chat_busy", "A tutor response is still in progress.")
    used = await db.scalar(select(func.coalesce(func.sum(ChatTurn.attempt_count), 0)).join(
        ChatSession, ChatSession.id == ChatTurn.session_id).where(ChatSession.user_id == user.id,
        ChatTurn.updated_at >= now() - dt.timedelta(minutes=1)))
    if used >= RATE:
        fail("chat_rate_limit", "Please wait before asking another question.", 429)
    task, context, context_info = await build_context(session, user, db)
    # Only completed prior turns enter model history; failed/pending prompts cannot masquerade as replies.
    associated_turn = select(ChatTurn.id).where(or_(ChatMessage.id == ChatTurn.user_message_id,
        ChatMessage.id == ChatTurn.assistant_message_id)).correlate(ChatMessage)
    history_rows = list((await db.scalars(select(ChatMessage).where(
        ChatMessage.session_id == session_id, ChatMessage.sender_type.in_([SenderType.user, SenderType.assistant]),
        or_(associated_turn.where(ChatTurn.status == "completed").exists(), ~associated_turn.exists()))
        .order_by(ChatMessage.id.desc()).limit(41))).all())
    context_info["truncated"] |= len(history_rows) > 40
    history = []
    remaining = 16000
    for message in history_rows[:40]:
        if len(message.content) > remaining:
            context_info["truncated"] = True
            break
        history.append(AIMessage(role=message.sender_type.value, content=message.content))
        remaining -= len(message.content)
    history.reverse()
    if not turn:
        message = ChatMessage(session_id=session_id, sender_type=SenderType.user, content=body.content)
        db.add(message)
        await db.flush()
        turn = ChatTurn(session_id=session_id, request_id=str(body.request_id), user_message_id=message.id,
                        attempt_count=0)
        db.add(turn)
    generation = str(uuid4())
    turn.status, turn.generation = "pending", generation
    turn.attempt_count += 1
    turn.lease_until = now() + dt.timedelta(seconds=TIMEOUT + 15)
    turn.updated_at, turn.error_code, turn.context_info = now(), None, context_info
    session.updated_at = now()
    await db.commit()  # Do not hold a database lock/transaction during a provider call.
    turn_id = turn.id
    started_at = time.monotonic()
    try:
        if task.type.value == "lab":
            payload = LabAssistantChatRequest(lab_title=task.title, lab_type=context_info["lab_mode"],
                steps_and_theory=context, model_answers="", chat_history=history,
                student_message=body.content, response_language=session.language)
            function = ai.lab_assistant_chat
        else:
            payload = SocraticChatRequest(task_title=task.title, reference_text=context,
                chat_history=history, student_message=body.content, response_language=session.language)
            function = ai.socratic_chat
        result = await asyncio.wait_for(call_ai(function, payload, context_truncated=context_info["truncated"]), timeout=TIMEOUT)
        if not result.reply.strip() or len(result.reply) > 16000:
            raise AIRubricError("Invalid tutor reply")
    except (AIServiceError, AIRubricError, AIRequestError, TimeoutError):
        await db.execute(update(ChatTurn).where(ChatTurn.id == turn_id, ChatTurn.generation == generation,
            ChatTurn.status == "pending").values(status="failed", error_code="ai_unavailable", updated_at=now()))
        await db.commit()
        fail("ai_unavailable", "Tutor unavailable. Your message was saved; retry explicitly.", 503)
    # Fencing prevents an expired/replaced provider attempt from publishing a late second response.
    turn = await db.scalar(select(ChatTurn).where(ChatTurn.id == turn_id).with_for_update().execution_options(populate_existing=True))
    if not turn or turn.generation != generation or turn.status != "pending" or turn.lease_until <= now():
        fail("chat_interrupted", "This response expired. Refresh before retrying.")
    reply = ChatMessage(session_id=session_id, sender_type=SenderType.assistant, content=result.reply)
    db.add(reply)
    await db.flush()
    turn.assistant_message_id, turn.status, turn.is_mock = reply.id, "completed", ai.engine.mock_mode
    metadata = result.ai_metadata
    turn.ai_metadata = {key: getattr(metadata, key, None) for key in (
        "provider", "model_used", "prompt_version", "ai_engine_version")}
    turn.ai_metadata.update(latency_ms=round((time.monotonic() - started_at) * 1000, 2),
                            output_sanitized=bool(getattr(metadata, "output_sanitized", False)))
    turn.updated_at = now()
    await db.commit()
    return await turn_info(turn, db)


async def legacy_messages(session_id, user, db, before, limit):
    await owned_session(session_id, user, db)
    associated = select(ChatTurn.id).where(or_(ChatTurn.user_message_id == ChatMessage.id,
        ChatTurn.assistant_message_id == ChatMessage.id)).correlate(ChatMessage).exists()
    query = select(ChatMessage).where(ChatMessage.session_id == session_id, ~associated,
                                     ChatMessage.sender_type.in_([SenderType.user, SenderType.assistant]))
    if before:
        query = query.where(ChatMessage.id < before)
    rows = list((await db.scalars(query.order_by(ChatMessage.id.desc()).limit(limit + 1))).all())
    return LegacyMessages(items=[LegacyMessage.model_validate(m) for m in reversed(rows[:limit])],
        next_cursor=rows[limit - 1].id if len(rows) > limit else None)


async def share_preview(session_id, through_turn_id, user, db):
    await owned_session(session_id, user, db)
    last = await db.get(ChatTurn, through_turn_id)
    if not last or last.session_id != session_id or last.status != "completed":
        fail("invalid_input", "Select a completed turn in this conversation.", 422)
    rows = list((await db.scalars(select(ChatTurn).where(ChatTurn.session_id == session_id,
        ChatTurn.id <= through_turn_id, ChatTurn.status == "completed").order_by(ChatTurn.id).limit(201))).all())
    if len(rows) > 200:
        fail("chat_share_too_large", "Share a shorter conversation (at most 200 completed turns).", 422)
    snapshot = []
    for turn in rows:
        item = await turn_info(turn, db)
        snapshot.append(SharedTurn(id=item.id, content=item.content, reply=item.reply,
                                  is_mock=item.is_mock, created_at=item.created_at))
    return snapshot


async def share_info(share, db, detail=False):
    session = await db.get(ChatSession, share.session_id)
    student, recipient = await db.get(User, session.user_id), await db.get(User, share.recipient_id)
    values = dict(id=share.id, session_id=session.id, task_id=session.task_id, title=session.title,
        student_name=student.name, recipient_name=recipient.name, through_turn_id=share.through_turn_id,
        created_at=share.created_at, revoked_at=share.revoked_at)
    return ShareDetail(**values, snapshot=share.snapshot) if detail else ShareInfo(**values)


async def create_share(session_id, body, user, db):
    await owned_session(session_id, user, db)
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -772)"), {"user": user.id})
    recipient = await db.scalar(select(User).where(func.lower(User.email) == str(body.recipient_email).lower(),
        User.role.in_([UserRole.professor, UserRole.teaching_assistant])))
    if not recipient:
        fail("share_recipient_missing", "Teaching staff recipient not found.", 404)
    old = await db.scalar(select(ChatShare).where(ChatShare.session_id == session_id,
        ChatShare.request_id == str(body.request_id)))
    if old:
        if (old.recipient_id, old.through_turn_id) != (recipient.id, body.through_turn_id):
            fail("request_conflict", "Share request was already used with different values.")
        return await share_info(old, db)
    snapshot = await share_preview(session_id, body.through_turn_id, user, db)
    if [item.id for item in snapshot] != body.preview_turn_ids:
        fail("request_conflict", "Conversation changed. Preview the snapshot again before sharing.")
    share = ChatShare(session_id=session_id, recipient_id=recipient.id, request_id=str(body.request_id),
                      through_turn_id=body.through_turn_id, snapshot=[s.model_dump(mode="json") for s in snapshot])
    db.add(share)
    await db.flush()
    from backend.services.account_service import audit
    audit(db, user.id, "chat.shared", "chat_share", share.id)
    await db.commit()
    return await share_info(share, db)


async def list_shares(user, db, before, limit, session_id=None):
    query = select(ChatShare)
    if session_id is not None:
        await owned_session(session_id, user, db)
        query = query.where(ChatShare.session_id == session_id)
    else:
        query = query.where(ChatShare.recipient_id == user.id, ChatShare.revoked_at.is_(None))
    if before:
        query = query.where(ChatShare.id < before)
    rows = list((await db.scalars(query.order_by(ChatShare.id.desc()).limit(limit + 1))).all())
    return ShareList(items=[await share_info(row, db) for row in rows[:limit]],
                     next_cursor=rows[limit - 1].id if len(rows) > limit else None)


async def read_share(share_id, user, db):
    share = await db.get(ChatShare, share_id)
    if not share or share.recipient_id != user.id or share.revoked_at is not None:
        fail("not_found", "Shared conversation not found.", 404)
    return await share_info(share, db, detail=True)


async def revoke_share(share_id, user, db):
    share = await db.scalar(select(ChatShare).where(ChatShare.id == share_id).with_for_update())
    if not share:
        fail("not_found", "Share not found.", 404)
    await owned_session(share.session_id, user, db)
    if share.revoked_at is None:
        from backend.services.account_service import audit
        audit(db, user.id, "chat.revoked", "chat_share", share.id)
        share.revoked_at = now()
    await db.commit()


async def tutor_settings(task_id, user, db, body=None):
    task = await _get_task(task_id, db)
    if task.type.value != "lab":
        fail("invalid_input", "Lab mode settings apply only to labs.", 422)
    # Serialize the first settings insert too, when no settings row exists yet.
    await db.execute(text("SELECT pg_advisory_xact_lock(:task, -773)"), {"task": task_id})
    settings = await db.get(TaskTutorSettings, task_id)
    if body:
        if not settings:
            settings = TaskTutorSettings(task_id=task_id, updated_by=user.id)
            db.add(settings)
        settings.lab_mode, settings.updated_by, settings.updated_at = body.lab_mode, user.id, now()
        await db.commit()
    return TutorSettings.model_validate(settings) if settings else TutorSettings()
