from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.dependencies import require_student, require_staff
from backend.database import get_db
from backend.models.users import User
from backend.schemas.chat import ChatCreate, ChatSend, ChatInfo, ChatList, ChatTurnInfo, ChatTurnList
from backend.schemas.chat import ShareCreate, ShareInfo, ShareDetail, ShareList, SharedTurn, TutorSettings, LegacyMessages
from backend.services import chat_service as service

router = APIRouter(tags=["Student tutoring"])


@router.post("/tasks/{task_id}/chat-sessions", response_model=ChatInfo, status_code=201)
async def create(task_id: int, body: ChatCreate, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.create_session(task_id, body, user, db)


@router.get("/tasks/{task_id}/chat-sessions", response_model=ChatList)
async def sessions(task_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                   user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.list_sessions(task_id, user, db, before, limit)


@router.get("/chat-sessions/{session_id}", response_model=ChatInfo)
async def detail(session_id: int, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.owned_session(session_id, user, db)


@router.get("/chat-sessions/{session_id}/messages", response_model=ChatTurnList)
async def messages(session_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                   user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.list_turns(session_id, user, db, before, limit)


@router.post("/chat-sessions/{session_id}/messages", response_model=ChatTurnInfo)
async def send(session_id: int, body: ChatSend, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.send_turn(session_id, body, user, db)


@router.get("/chat-sessions/{session_id}/legacy-messages", response_model=LegacyMessages)
async def legacy(session_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                 user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.legacy_messages(session_id, user, db, before, limit)


@router.get("/chat-sessions/{session_id}/share-preview", response_model=list[SharedTurn])
async def preview(session_id: int, through_turn_id: int = Query(gt=0), user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.share_preview(session_id, through_turn_id, user, db)


@router.post("/chat-sessions/{session_id}/shares", response_model=ShareInfo, status_code=201)
async def share(session_id: int, body: ShareCreate, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.create_share(session_id, body, user, db)


@router.get("/chat-sessions/{session_id}/shares", response_model=ShareList)
async def owner_shares(session_id: int, before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                       user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    return await service.list_shares(user, db, before, limit, session_id)


@router.delete("/chat-shares/{share_id}", status_code=204)
async def revoke(share_id: int, user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    await service.revoke_share(share_id, user, db)


@router.get("/chat-shares", response_model=ShareList)
async def received_shares(before: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                          user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.list_shares(user, db, before, limit)


@router.get("/chat-shares/{share_id}", response_model=ShareDetail)
async def shared_detail(share_id: int, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.read_share(share_id, user, db)


@router.get("/tasks/{task_id}/tutor-settings", response_model=TutorSettings)
async def settings(task_id: int, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.tutor_settings(task_id, user, db)


@router.patch("/tasks/{task_id}/tutor-settings", response_model=TutorSettings)
async def update_settings(task_id: int, body: TutorSettings, user: User = Depends(require_staff), db: AsyncSession = Depends(get_db)):
    return await service.tutor_settings(task_id, user, db, body)
