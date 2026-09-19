"""Consented rosters. Team membership never grants access to another student's assessment."""
import datetime as dt
import hashlib
import json
from sqlalchemy import select, text, or_
from backend.models.teams import Team, TeamMember, TeamInvitation, TeamEvent
from backend.models.users import Student, User
from backend.models.enums import UserRole
from backend.repository.task_repository import _get_task
from backend.schemas.team import (RosterMember, TeamSnapshot, TeamInfo, TeamList, InvitationInfo,
    InvitationList, TeamMutationResult, TeamEventInfo, TeamEventList)
from backend.services.access import check_task_access, fail, student_user


def now():
    return dt.datetime.now(dt.timezone.utc)


def staff(user):
    return user.role in (UserRole.professor, UserRole.teaching_assistant)


async def lock_rosters(task_id, db):
    await db.execute(text("SELECT pg_advisory_xact_lock(:task, -776)"), {"task": task_id})


async def project(task_id, user, db):
    task = await _get_task(task_id, db)
    check_task_access(task, user)
    if not task.project_details or not task.project_details.require_team:
        fail("team_not_required", "Teams are available for team-required projects only.", 422)
    return task


async def active_team(task_id, student_id, db):
    return await db.scalar(select(Team).join(TeamMember, TeamMember.team_id == Team.id).where(
        TeamMember.task_id == task_id, TeamMember.student_id == student_id, TeamMember.active.is_(True))
        .execution_options(populate_existing=True))


async def submission_team(task, user, db):
    team = await active_team(task.id, user.id, db)
    if not team:
        return None, "team_required"
    if team.status == "legacy":
        return team, "team_legacy_review"
    member = await db.get(TeamMember, (team.id, user.id), populate_existing=True)
    if team.status != "approved" or not team.approved_roster or not member.accepted_at:
        return team, "team_not_approved"
    return team, None


async def roster(team, db):
    rows = (await db.execute(select(TeamMember, User, Student).join(User, User.id == TeamMember.student_id)
        .join(Student, Student.user_id == User.id).where(TeamMember.team_id == team.id, TeamMember.active.is_(True))
        .order_by(TeamMember.student_id))).all()
    return [RosterMember(student_id=m.student_id, name=u.name, student_number=s.student_number,
                         accepted_at=m.accepted_at) for m, u, s in rows]


async def snapshot(team, db):
    return TeamSnapshot(team_id=team.id, name=team.name, version=team.version, members=await roster(team, db))


async def invitation_info(row, db):
    team, user = await db.get(Team, row.team_id), await db.get(User, row.student_id)
    return InvitationInfo(id=row.id, team_id=team.id, task_id=team.task_id, team_name=team.name,
        student_id=row.student_id, name=user.name, status=row.status, created_at=row.created_at)


async def visible(team, user, db):
    await project(team.task_id, user, db)
    if staff(user) or team.created_by == user.id:
        return
    member = await db.get(TeamMember, (team.id, user.id), populate_existing=True)
    invited = await db.scalar(select(TeamInvitation.id).where(TeamInvitation.team_id == team.id,
        TeamInvitation.student_id == user.id, TeamInvitation.status == "pending").limit(1))
    if not (member and member.active) and not invited:
        fail("not_found", "Team not found.", 404)


async def load_team(team_id, db, lock=False):
    team = await db.get(Team, team_id)
    if not team:
        fail("not_found", "Team not found.", 404)
    if lock:
        await lock_rosters(team.task_id, db)
        await db.refresh(team)
    return team


async def team_info(team, user, db):
    members = await roster(team, db)
    invitations = list((await db.scalars(select(TeamInvitation).where(TeamInvitation.team_id == team.id,
        TeamInvitation.status == "pending").order_by(TeamInvitation.id))).all())
    actions, reason = [], None
    if team.status == "legacy":
        reason = "team_legacy_review"
    elif team.locked_at:
        reason = "team_locked"
    elif team.status == "archived":
        reason = "team_archived"
    elif staff(user):
        if team.status == "awaiting_approval":
            actions = ["approve", "reject"]
    elif team.created_by == user.id:
        actions = ["invite", "remove", "cancel_invitation", "archive"]
        if not invitations and members and all(m.accepted_at for m in members) and team.status in ("draft", "rejected"):
            actions.append("request_approval")
    elif any(m.student_id == user.id for m in members):
        actions = ["leave"]
    return TeamInfo(id=team.id, task_id=team.task_id, name=team.name, created_by=team.created_by,
        status=team.status, version=team.version, locked_at=team.locked_at, members=members,
        invitations=[await invitation_info(i, db) for i in invitations], actions=actions, unavailable_reason=reason)


async def detail(team_id, user, db):
    team = await load_team(team_id, db)
    await visible(team, user, db)
    return await team_info(team, user, db)


async def list_teams(task_id, user, db, before, limit, status):
    await project(task_id, user, db)
    query = select(Team).where(Team.task_id == task_id)
    if not staff(user):
        member_ids = select(TeamMember.team_id).where(TeamMember.student_id == user.id, TeamMember.active.is_(True))
        invitations = select(TeamInvitation.team_id).where(TeamInvitation.student_id == user.id, TeamInvitation.status == "pending")
        query = query.where(or_(Team.created_by == user.id, Team.id.in_(member_ids), Team.id.in_(invitations)))
    if status:
        query = query.where(Team.status == status)
    if before:
        query = query.where(Team.id < before)
    rows = list((await db.scalars(query.order_by(Team.id.desc()).limit(limit + 1))).all())
    return TeamList(items=[await team_info(t, user, db) for t in rows[:limit]],
                    next_cursor=rows[limit-1].id if len(rows) > limit else None)


async def inbox(user, db, before, limit):
    from backend.models.tasks import Task
    query = select(TeamInvitation).join(Team, Team.id == TeamInvitation.team_id).join(Task, Task.id == Team.task_id).where(
        TeamInvitation.student_id == user.id, TeamInvitation.status == "pending",
        Task.target_cohort_year == user.student.cohort_year,
        or_(Task.target_major.is_(None), Task.target_major == user.student.major))
    if before:
        query = query.where(TeamInvitation.id < before)
    rows = list((await db.scalars(query.order_by(TeamInvitation.id.desc()).limit(limit + 1))).all())
    return InvitationList(items=[await invitation_info(i, db) for i in rows[:limit]],
                          next_cursor=rows[limit-1].id if len(rows) > limit else None)


def fingerprint(team_id, payload):
    return hashlib.sha256(json.dumps([team_id, payload], sort_keys=True).encode()).hexdigest()


async def replay(team, body, user, db, extra=None):
    data = body.model_dump(mode="json")
    if extra:
        data.update(extra)
    digest = fingerprint(team.id, data)
    old = await db.scalar(select(TeamEvent).where(TeamEvent.actor_id == user.id, TeamEvent.request_id == str(body.request_id)))
    if old:
        if old.team_id != team.id or old.request_hash != digest:
            fail("request_conflict", "Request ID was already used differently.")
        return TeamMutationResult(team_id=team.id, version=old.version), digest
    return None, digest


async def record(team, body, user, db, action, digest):
    await db.flush()
    from backend.services.account_service import audit
    audit(db, user.id, "team." + action, "team", team.id)
    db.add(TeamEvent(team_id=team.id, actor_id=user.id, request_id=str(body.request_id), request_hash=digest,
        action=action, version=team.version, roster=(await snapshot(team, db)).model_dump(mode="json")))
    await db.commit()
    return TeamMutationResult(team_id=team.id, version=team.version)


def editable(team):
    if team.status == "legacy":
        fail("team_legacy_review", "Historical roster requires reviewed consent; no automatic approvals.")
    if team.locked_at:
        fail("team_locked", "The first team-linked submission permanently locked this roster.")
    if team.status == "archived":
        fail("team_archived", "This team is archived.")


def version_check(team, body):
    if team.version != body.expected_version:
        fail("team_changed", "The roster changed. Review it again before acting.")


def invalidate(team):
    team.status, team.approved_roster = "draft", None


async def complete_roster(team, user, db):
    task = await project(team.task_id, user, db)
    members = await roster(team, db)
    pending = await db.scalar(select(TeamInvitation.id).where(TeamInvitation.team_id == team.id, TeamInvitation.status == "pending").limit(1))
    if not members or pending or any(not m.accepted_at for m in members):
        fail("team_consent_required", "Every invited member must accept before requesting approval.")
    for member in members:
        check_task_access(task, await student_user(member.student_id, db))


async def create(task_id, body, user, db):
    await project(task_id, user, db)
    # Serialize request IDs across tasks too, then take the task roster lock in fixed order.
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -777)"), {"user": user.id})
    await lock_rosters(task_id, db)
    old = await db.scalar(select(Team).where(Team.created_by == user.id, Team.request_id == str(body.request_id)))
    if old:
        if old.task_id != task_id or old.name != body.name:
            fail("request_conflict", "Request ID already used.")
        return await team_info(old, user, db)
    if await db.scalar(select(TeamEvent.id).where(TeamEvent.actor_id == user.id, TeamEvent.request_id == str(body.request_id))):
        fail("request_conflict", "Request ID already used for another team operation.")
    if await active_team(task_id, user.id, db):
        fail("team_membership_exists", "You already belong to a team for this project.")
    team = Team(task_id=task_id, name=body.name, created_by=user.id, request_id=str(body.request_id), status="draft")
    db.add(team)
    await db.flush()
    db.add(TeamMember(team_id=team.id, task_id=task_id, student_id=user.id, accepted_at=now()))
    await db.flush()
    await record(team, body, user, db, "create", fingerprint(team.id, body.model_dump(mode="json")))
    return await team_info(team, user, db)


async def act(team_id, body, user, db):
    # One operation per actor prevents request-ID races across different tasks.
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -777)"), {"user": user.id})
    team = await load_team(team_id, db, lock=True)
    await project(team.task_id, user, db)
    old, digest = await replay(team, body, user, db)
    if old:
        return old
    await visible(team, user, db)
    editable(team)
    version_check(team, body)
    action = body.action
    if action in ("approve", "reject"):
        if not staff(user):
            fail("permission_denied", "Teaching staff approval required.", 403)
        if team.status != "awaiting_approval":
            fail("team_changed", "This roster is not awaiting approval.")
        await complete_roster(team, user, db)
        team.status = "approved" if action == "approve" else "rejected"
    elif action == "leave":
        member = await db.get(TeamMember, (team.id, user.id))
        if team.created_by == user.id or not member or not member.active:
            fail("permission_denied", "Owners archive the team; only active members can leave.", 403)
        member.active = False
        invalidate(team)
    else:
        if team.created_by != user.id or user.role != UserRole.student:
            fail("permission_denied", "Only the student team owner can manage the roster.", 403)
        if action == "invite":
            target = await db.scalar(select(Student).where(Student.student_number == body.student_number))
            if not target:
                fail("team_student_unavailable", "Eligible student not available.", 404)
            target_user = await student_user(target.user_id, db)
            task = await _get_task(team.task_id, db)
            if target.cohort_year != task.target_cohort_year or (task.target_major and target.major != task.target_major):
                fail("team_student_unavailable", "Eligible student not available.", 404)
            if await active_team(team.task_id, target.user_id, db):
                fail("team_membership_exists", "Student already belongs to a project team.")
            pending = list((await db.scalars(select(TeamInvitation).where(TeamInvitation.team_id == team.id,
                TeamInvitation.status == "pending"))).all())
            if any(i.student_id == target_user.id for i in pending):
                fail("team_invitation_exists", "This invitation is already pending.")
            if len(await roster(team, db)) + len(pending) >= 20:
                fail("team_limit", "At most 20 members and pending invitations are supported.", 422)
            db.add(TeamInvitation(team_id=team.id, student_id=target_user.id))
            invalidate(team)
        elif action == "remove":
            member = await db.get(TeamMember, (team.id, body.student_id))
            if not member or not member.active or member.student_id == team.created_by:
                fail("invalid_input", "Choose an active member other than the owner.", 422)
            member.active = False
            invalidate(team)
        elif action == "cancel_invitation":
            invitation = await db.get(TeamInvitation, body.invitation_id)
            if not invitation or invitation.team_id != team.id or invitation.status != "pending":
                fail("team_changed", "Invitation is no longer pending.")
            invitation.status, invitation.responded_at = "cancelled", now()
            invalidate(team)
        elif action == "archive":
            for member in (await db.scalars(select(TeamMember).where(TeamMember.team_id == team.id))).all():
                member.active = False
            for invitation in (await db.scalars(select(TeamInvitation).where(TeamInvitation.team_id == team.id,
                TeamInvitation.status == "pending"))).all():
                invitation.status, invitation.responded_at = "cancelled", now()
            team.status, team.approved_roster = "archived", None
        elif action == "request_approval":
            if team.status not in ("draft", "rejected"):
                fail("team_changed", "This team cannot request approval in its current state.")
            await complete_roster(team, user, db)
            team.status = "awaiting_approval"
    team.version += 1
    if action == "approve":
        team.approved_roster = (await snapshot(team, db)).model_dump(mode="json")
    return await record(team, body, user, db, action, digest)


async def respond(invitation_id, body, user, db):
    await db.execute(text("SELECT pg_advisory_xact_lock(:user, -777)"), {"user": user.id})
    invitation = await db.get(TeamInvitation, invitation_id)
    if not invitation or invitation.student_id != user.id:
        fail("not_found", "Invitation not found.", 404)
    team = await load_team(invitation.team_id, db, lock=True)
    await db.refresh(invitation)
    await project(team.task_id, user, db)
    old, digest = await replay(team, body, user, db, {"invitation_id": invitation_id})
    if old:
        return old
    editable(team)
    version_check(team, body)
    if invitation.status != "pending":
        fail("team_changed", "This invitation is no longer pending.")
    if body.decision == "accept":
        if await active_team(team.task_id, user.id, db):
            fail("team_membership_exists", "Leave your existing team before accepting another invitation.")
        member = await db.get(TeamMember, (team.id, user.id))
        if not member:
            member = TeamMember(team_id=team.id, task_id=team.task_id, student_id=user.id)
            db.add(member)
        member.active, member.accepted_at = True, now()
    invitation.status = "accepted" if body.decision == "accept" else "declined"
    invitation.responded_at = now()
    invalidate(team)
    team.version += 1
    return await record(team, body, user, db, body.decision, digest)


async def history(team_id, user, db, before, limit):
    team = await load_team(team_id, db)
    await visible(team, user, db)
    # Invitees preview the current roster, not its historical member identities.
    member = await db.get(TeamMember, (team.id, user.id))
    if not staff(user) and team.created_by != user.id and not (member and member.active):
        fail("permission_denied", "Current membership is required for roster history.", 403)
    query = select(TeamEvent).where(TeamEvent.team_id == team_id)
    if before:
        query = query.where(TeamEvent.id < before)
    rows = list((await db.scalars(query.order_by(TeamEvent.id.desc()).limit(limit + 1))).all())
    return TeamEventList(items=[TeamEventInfo.model_validate(r) for r in rows[:limit]],
        next_cursor=rows[limit-1].id if len(rows) > limit else None)
