"""LifeLessonPlan 後端。提供老師登入、登出、素材庫、學生與預設關卡。"""

import os
import secrets
from pathlib import Path

import pymysql
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.auth import SESSIONS, bearer, current_teacher_id, get_teacher, password_matches
from backend.database import STATIC_DIR, db_conn
from backend.generate import router as generate_router
from backend.library import router as library_router
from backend.material import router as material_router
from backend.students import router as students_router
from backend.unity import router as unity_router
from backend.workflow import router as workflow_router

# src/backend/main.py → Final/frontend
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"

app = FastAPI(title="LifeLessonPlan API")

app.include_router(library_router)
app.include_router(generate_router)
app.include_router(unity_router)
app.include_router(workflow_router)
app.include_router(students_router)
app.include_router(material_router)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health() -> dict[str, str]:
    """確認服務已啟動。不連線資料庫。"""
    return {"status": "ok"}


@app.get("/api/db-check")
def db_check() -> dict[str, object]:
    """確認 .env 的連線設定可連到 MariaDB。"""
    try:
        with db_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION() AS version")
                row = cursor.fetchone()
    except pymysql.Error as error:
        return {"connected": False, "error": str(error)}
    return {"connected": True, "version": row["version"], "database": os.getenv("DB_NAME")}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, object]:
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password_hash FROM Teacher WHERE username = %s",
                (payload.username.strip(),),
            )
            teacher = cursor.fetchone()

    # 帳號不存在與密碼錯誤回傳同一則訊息。回應不顯示帳號是否存在。
    if teacher is None or not password_matches(payload.password, teacher["password_hash"]):
        raise HTTPException(status_code=401, detail="帳號或密碼不對")

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = teacher["id"]
    return {"token": token, "teacher": {"id": teacher["id"], "username": teacher["username"]}}


@app.post("/api/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, str]:
    # 未帶 token 也回傳 ok。前端清除 localStorage 後視為登出成功。
    if credentials:
        SESSIONS.pop(credentials.credentials, None)
    return {"status": "ok"}


@app.get("/api/me")
def me(teacher_id: int = Depends(current_teacher_id)) -> dict[str, object]:
    """回傳目前登入的老師。前端用此檢查登入狀態。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            return get_teacher(cursor, teacher_id)


# /static 提供圖檔。前端掛在最後。此順序不攔截 /api 與 /static。
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
