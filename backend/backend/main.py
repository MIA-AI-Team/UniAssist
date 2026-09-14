
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.auth import router as auth_router
from backend.routers.rubric import router as rubrics_router
from backend.routers.task import router as tasks_router
from backend.routers.file import router as files_router
from backend.routers.submission import router as submissions_router

app = FastAPI(
    title="UniAssist API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(files_router)
app.include_router(submissions_router)
app.include_router(rubrics_router)




@app.get("/health")
async def health():
    return {"status": "ok"}