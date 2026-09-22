"""老師登入狀態。main 與其他路由共用此模組。"""

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# token 對應 teacher_id。只存在記憶體。後端重啟後必須重新登入。
SESSIONS: dict[str, int] = {}

# auto_error=False：未帶 Authorization 時不立刻回 403。由此函式回 401。
bearer = HTTPBearer(auto_error=False)


def password_matches(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        # 不是 bcrypt 的雜湊一律當密碼錯誤。
        return False


def current_teacher_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> int:
    """從 Authorization: Bearer <token> 取得目前登入的老師。"""
    teacher_id = SESSIONS.get(credentials.credentials) if credentials else None
    if teacher_id is None:
        raise HTTPException(status_code=401, detail="請重新登入")
    return teacher_id


def get_teacher(cursor, teacher_id: int) -> dict:
    cursor.execute("SELECT id, username FROM Teacher WHERE id = %s", (teacher_id,))
    teacher = cursor.fetchone()
    if teacher is None:
        raise HTTPException(status_code=401, detail="請重新登入")
    return teacher
