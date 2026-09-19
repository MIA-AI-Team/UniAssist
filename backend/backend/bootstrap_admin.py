"""Operator-only: python -m backend.bootstrap_admin (interactive, no password arguments)."""
import asyncio
import getpass
from pydantic import TypeAdapter, EmailStr
from sqlalchemy import select
from backend.database import AsyncSessionLocal, engine
from backend.models.users import User, Admin
from backend.core.security import hash_password
from backend.services.account_service import account_lock, audit


async def bootstrap(name, email, password):
    async with AsyncSessionLocal() as db:
        await account_lock(db)
        if await db.scalar(select(User.id).where(User.email == email)):
            raise ValueError("Email already exists. Bootstrap never converts or overwrites an account.")
        user = User(name=name, email=email, password_hash=hash_password(password), role="admin")
        db.add(user)
        await db.flush()
        db.add(Admin(user_id=user.id, permission_level="standard"))
        audit(db, None, "admin.bootstrapped", "user", user.id)
        await db.commit()
        return user.id


async def main():
    try:
        name = input("Admin name: ").strip()
        email = str(TypeAdapter(EmailStr).validate_python(input("Admin email: ").strip()))
        password = getpass.getpass("Password (at least 12 characters): ")
        if not 2 <= len(name) <= 150 or len(password) < 12 or password != getpass.getpass("Confirm password: "):
            raise ValueError("Invalid name or mismatched/short password.")
        user_id = await bootstrap(name, email, password)
        print(f"Created admin account {user_id}. No existing account was changed.")
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
