
from fastapi import FastAPI, Depends
from backend.core.dependencies import require_academic
from backend.routers.admin import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from backend.services.exceptions import NoAcceptedRubric, AIRequestError, AIRubricError, AIServiceError

from backend.routers.auth import router as auth_router
from backend.routers.rubric import router as rubrics_router
from backend.routers.task import router as tasks_router
from backend.routers.file import router as files_router
from backend.routers.submission import router as submissions_router
from backend.routers.chat import router as chat_router
from backend.routers.teaching import router as teaching_router
from backend.routers.team import router as team_router
from backend.routers.repository import router as repository_router

app = FastAPI(
    title="UniAssist API",
    version="0.1.0",
)

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    codes = {400: "invalid_input", 401: "session_expired", 403: "permission_denied", 404: "not_found",
             409: "conflict", 422: "invalid_input", 502: "ai_invalid_response", 503: "ai_unavailable"}
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail,
        "code": (exc.headers or {}).get("X-Error-Code", codes.get(exc.status_code, "request_failed"))}, headers=exc.headers)

async def service_error(request: Request, exc: Exception):
    status, code = {NoAcceptedRubric: (409, "rubric_not_ready"), AIRequestError: (422, "invalid_input"),
        AIRubricError: (502, "ai_invalid_response"), AIServiceError: (503, "ai_unavailable")}[type(exc)]
    messages = {"rubric_not_ready": "A professor must accept a rubric before submission.",
        "invalid_input": "AI input could not be processed.",
        "ai_invalid_response": "AI returned an unusable response. Please retry.",
        "ai_unavailable": "AI is temporarily unavailable. Please retry later."}
    return JSONResponse(status_code=status, content={"detail": messages[code], "code": code})

for error in (NoAcceptedRubric, AIRequestError, AIRubricError, AIServiceError):
    app.add_exception_handler(error, service_error)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
for academic_router in (tasks_router, files_router, submissions_router, rubrics_router,
                        chat_router, teaching_router, team_router, repository_router):
    app.include_router(academic_router, dependencies=[Depends(require_academic)])




@app.get("/health")
async def health():
    return {"status": "ok"}
