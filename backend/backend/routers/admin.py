import datetime as dt
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.dependencies import require_admin
from backend.database import get_db
from backend.models.users import User
from backend.models.operations import AuditEvent, AIOperation
from backend.schemas.accounts import AccountInfo, AccountList, AccountUpdate, AuditList, MetricsResponse
from backend.services.account_service import load_account, account_info, search_accounts, update_account

router = APIRouter(prefix="/admin", tags=["Account operations"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=AccountList)
async def users(q: str = Query("", max_length=150), before: int | None = Query(None, ge=1),
                limit: int = Query(30, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await search_accounts(db, q.strip(), before, limit)


@router.get("/users/{user_id}", response_model=AccountInfo)
async def user_detail(user_id: int, db: AsyncSession = Depends(get_db)):
    return account_info(await load_account(user_id, db))


@router.patch("/users/{user_id}", response_model=AccountInfo)
async def correct(user_id: int, body: AccountUpdate, actor: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return account_info(await update_account(user_id, body, actor, db, admin=True))


@router.get("/audit", response_model=AuditList)
async def audit(before: int | None = Query(None, ge=1), limit: int = Query(30, ge=1, le=100),
                db: AsyncSession = Depends(get_db)):
    query = select(AuditEvent)
    if before:
        query = query.where(AuditEvent.id < before)
    rows = list((await db.scalars(query.order_by(AuditEvent.id.desc()).limit(limit + 1))).all())
    return {"items": rows[:limit], "next_cursor": rows[limit - 1].id if len(rows) > limit else None}


@router.get("/ai-metrics", response_model=MetricsResponse)
async def metrics(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db)):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    rows = (await db.execute(select(AIOperation.operation, AIOperation.provider,
        func.count().label("calls"),
        func.count().filter(AIOperation.outcome == "error").label("errors"),
        func.count().filter(AIOperation.outcome == "started").label("incomplete"),
        func.coalesce(func.avg(AIOperation.latency_ms).filter(AIOperation.outcome != "started"), 0).label("average_latency_ms"),
        func.count().filter(AIOperation.is_mock.is_(True)).label("mock_calls"),
        func.count().filter(AIOperation.is_mock.is_(None)).label("unknown_mock_calls"),
        func.count().filter(AIOperation.truncated.is_(True)).label("truncated_calls"),
        func.count().filter(AIOperation.truncated.is_(None)).label("unknown_truncation_calls"))
        .where(AIOperation.created_at >= since).group_by(AIOperation.operation, AIOperation.provider)
        .order_by(AIOperation.operation, AIOperation.provider))).mappings().all()
    return {"since": since, "groups": [dict(r) for r in rows]}
