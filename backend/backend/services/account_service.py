"""Narrow account administration; history records field names, never field values."""
from sqlalchemy import select, text, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from backend.models.users import User, Student
from backend.models.operations import AuditEvent
from backend.schemas.auth import IdentityResponse
from backend.schemas.accounts import AccountInfo
from backend.services.access import fail


def audit(db, actor_id, action, target_type, target_id, fields=()):
    db.add(AuditEvent(actor_id=actor_id, action=action, target_type=target_type,
                      target_id=target_id, fields=sorted(fields)))


def identity(user):
    return IdentityResponse(id=user.id, name=user.name, email=user.email, role=user.role,
        student_number=user.student.student_number if user.student else None,
        cohort_year=user.student.cohort_year if user.student else None,
        major=user.student.major if user.student else None,
        github_username=user.student.github_username if user.student else None,
        department=user.staff.department if user.staff else None, profile_version=user.profile_version)


def account_info(user):
    return AccountInfo(**identity(user).model_dump(), is_active=user.is_active, created_at=user.created_at)


async def load_account(user_id, db):
    user = await db.scalar(select(User).where(User.id == user_id).options(
        selectinload(User.student), selectinload(User.staff)).execution_options(populate_existing=True))
    if not user:
        fail("not_found", "Account not found.", 404)
    return user


async def account_lock(db):
    # One short transaction serializes bootstrap, profile edits and admin status changes.
    await db.execute(text("SELECT pg_advisory_xact_lock(-778, -778)"))


async def update_account(user_id, body, actor, db, admin=False):
    await account_lock(db)
    current_actor = await load_account(actor.id, db)
    if not current_actor.is_active:
        fail("account_suspended", "Account is suspended.", 401)
    if admin and current_actor.role != "admin":
        fail("permission_denied", "Admin required.", 403)
    user = await load_account(user_id, db)
    if user.profile_version != body.expected_version:
        fail("account_changed", "Account changed. Refresh before applying corrections.")
    changes = body.model_dump(exclude_unset=True, exclude={"expected_version"})
    if "role" in changes and user.role not in ("professor", "teaching_assistant"):
        fail("account_role_restricted", "Only TA/professor role changes are allowed.", 422)
    student_fields = {"student_number", "cohort_year", "major", "github_username"}
    if student_fields.intersection(changes) and not user.student:
        # Self-service sends null GitHub for non-students; reject all actual GitHub changes.
        if not admin and changes.get("github_username") is None:
            changes.pop("github_username", None)
        else:
            fail("invalid_input", "Student fields require a student account.", 422)
    if "department" in changes and not user.staff:
        fail("invalid_input", "Department requires teaching staff.", 422)
    if changes.get("is_active") is False and user.role == "admin" and user.is_active:
        count = await db.scalar(select(func.count()).select_from(User).where(User.role == "admin", User.is_active.is_(True)))
        if count <= 1:
            fail("last_active_admin", "The last active admin cannot be suspended.")
    changed = []
    for key, value in changes.items():
        target = user.student if key in student_fields else user.staff if key == "department" else user
        if getattr(target, key) != value:
            setattr(target, key, value)
            changed.append(key)
    if "role" in changed:
        user.staff.staff_role = user.role
    if changed:
        user.profile_version += 1
        audit(db, actor.id, "account.corrected" if admin else "profile.updated", "user", user.id, changed)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        fail("account_identifier_taken", "Email or student number is already in use.")
    return user


async def search_accounts(db, query, before, limit):
    statement = select(User).outerjoin(Student, Student.user_id == User.id).options(
        selectinload(User.student), selectinload(User.staff))
    if query:
        statement = statement.where(or_(User.name.icontains(query, autoescape=True),
            User.email.icontains(query, autoescape=True), Student.student_number.icontains(query, autoescape=True)))
    if before:
        statement = statement.where(User.id < before)
    rows = list((await db.scalars(statement.order_by(User.id.desc()).limit(limit + 1))).all())
    return {"items": [account_info(u) for u in rows[:limit]],
            "next_cursor": rows[limit - 1].id if len(rows) > limit else None}
