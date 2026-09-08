import os
from typing import Annotated
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Core Dependencies & Models
from backend.core.dependencies import get_current_user, require_roles
from backend.models.users import User
import uvicorn

# Routers
from backend.routers.auth import router as auth_router

app = FastAPI(title="UniAssist API", version="1.0.0")

# --- MIDDLEWARE & STORAGE SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ROUTER REGISTRATION ---
app.include_router(auth_router, prefix="/api", tags=["Authentication"])



# --- CORE / PROTECTED ROUTES ---
@app.get("/users/me", tags=["Users"])
async def get_my_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


@app.get("/admin/dashboard", tags=["Admin"])
async def admin_dashboard(
    current_user: Annotated[User, Depends(require_roles(["admin"]))]
):
    return {"message": f"Welcome Admin {current_user.name}"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)