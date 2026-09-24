"""老師的學生名單。Customization 使用 teacher_id 與 student_id。沒有學生時無法儲存自訂資料。"""

import pymysql
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import current_teacher_id, get_teacher
from backend.database import db_conn
from backend.storage import delete_custom_student_json

router = APIRouter(prefix="/api", tags=["students"])


class StudentRequest(BaseModel):
    username: str = Field(min_length=1, max_length=150)


def get_owned_student(cursor, teacher_id: int, student_id: int) -> dict:
    """確認 URL 中的學生屬於這位老師。"""
    cursor.execute(
        "SELECT id, username FROM Student WHERE id = %s AND teacher_id = %s",
        (student_id, teacher_id),
    )
    student = cursor.fetchone()
    if student is None:
        raise HTTPException(status_code=404, detail="找不到這位學生")
    return student


@router.get("/students")
def list_students(teacher_id: int = Depends(current_teacher_id)) -> list[dict[str, object]]:
    """只回傳這位老師的學生。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username FROM Student WHERE teacher_id = %s ORDER BY username",
                (teacher_id,),
            )
            return cursor.fetchall()


@router.post("/students", status_code=201)
def create_student(
    payload: StudentRequest, teacher_id: int = Depends(current_teacher_id)
) -> dict[str, object]:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="請輸入學生帳號")
    # 老師後台不設定學生密碼。password_hash 留空。學生端登入時再寫入。

    try:
        with db_conn(commit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Student (teacher_id, username, password_hash) VALUES (%s, %s, %s)",
                    (teacher_id, username, ""),
                )
                student_id = cursor.lastrowid
    except pymysql.IntegrityError:
        # Student.username 全域唯一。其他老師已使用相同帳號時也會失敗。
        raise HTTPException(status_code=409, detail=f"帳號「{username}」已經有人使用")
    return {"id": student_id, "username": username}


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int, teacher_id: int = Depends(current_teacher_id)
) -> dict[str, str]:
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            student = get_owned_student(cursor, teacher_id, student_id)
            teacher = get_teacher(cursor, teacher_id)
            # 兩張 customization 表參照 Student。這兩張表沒有 ON DELETE CASCADE。
            # 必須先刪除 customization 列，才能刪除學生。
            # 條件含 teacher_id。此刪除不修改其他老師的資料。
            cursor.execute(
                "DELETE FROM GameMaterialCustomization WHERE student_id = %s AND teacher_id = %s",
                (student_id, teacher_id),
            )
            cursor.execute(
                "DELETE FROM GameWorkflowCustomization WHERE student_id = %s AND teacher_id = %s",
                (student_id, teacher_id),
            )
            cursor.execute(
                "DELETE FROM Student WHERE id = %s AND teacher_id = %s",
                (student_id, teacher_id),
            )

    delete_custom_student_json(
        "GameWorkflowCustomization", teacher["username"], student["username"]
    )
    delete_custom_student_json(
        "GameMaterialCustomization", teacher["username"], student["username"]
    )
    return {"status": "deleted"}
