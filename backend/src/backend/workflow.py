"""關卡流程。全站使用 Default。老師可為學生儲存故事線。

JSON 放在 storage/。有自訂檔時使用自訂檔。沒有自訂檔時使用 Default。
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import current_teacher_id, get_teacher
from backend.database import db_conn
from backend.storage import (
    clean_dialogue_lines,
    parse_json_file,
    read_json_file,
    require_safe_name,
    storage_file,
)
from backend.students import get_owned_student

router = APIRouter(prefix="/api", tags=["workflow"])

# GameWorkflowDefault 沒有列時使用此相對路徑。對應 storage/ 下的種子檔。
FALLBACK_PATH = "GameWorkflowDefault/workflow.json"
KNOWN_GAMES = {
    "MarketShopping",
    "MemoryMatch",
    "PairVacuum",
    "SortArena",
    "DecisionParkour",
    "MarketShoppingBudgetMode",
}


class WorkflowStepIn(BaseModel):
    game: str
    gameMaterialCustomizationId: int | None = None
    order: int
    endNpcName: str = ""
    endDialogues: list[str] = Field(default_factory=list)


class StorylineIn(BaseModel):
    name: str = ""
    order: int
    steps: list[WorkflowStepIn] = Field(default_factory=list)


class WorkflowIn(BaseModel):
    startNpcName: str = ""
    startDialogues: list[str] = Field(default_factory=list)
    storylines: list[StorylineIn] = Field(default_factory=list)


def load_default_payload() -> dict:
    with db_conn() as connection:
        with connection.cursor() as cursor:
            # 此表只應有一筆預設。多列時取 id 最小的一筆。測試不要再 INSERT。
            cursor.execute("SELECT json_path FROM GameWorkflowDefault ORDER BY id LIMIT 1")
            row = cursor.fetchone()
    # 資料庫沒有列時，仍讀取 FALLBACK_PATH 指向的檔。
    relative = row["json_path"] if row else FALLBACK_PATH
    return read_json_file(relative, "找不到預設關卡設定")


def workflow_custom_path(teacher_username: str, student_username: str) -> str:
    """路徑由後端產生。不接受 client 指定的路徑。"""
    teacher_username = require_safe_name(teacher_username)
    student_username = require_safe_name(student_username)
    return f"GameWorkflowCustomization/{teacher_username}/{student_username}/workflow.json"


def require_consecutive_orders(orders: list[int]) -> None:
    """同一層的 order 必須從 1 起連續。同一層的 order 不可重複。"""
    if sorted(orders) != list(range(1, len(orders) + 1)):
        raise HTTPException(status_code=400, detail="order 必須從 1 起連續且不重複")


def require_student_material(
    cursor, teacher_id: int, student_id: int, game_code: str, config_id: int
) -> None:
    """確認這筆素材屬於這位學生。遊戲必須與關卡相同。"""
    cursor.execute(
        """
        SELECT Game.game_code
        FROM GameMaterialCustomization
        JOIN Game ON Game.id = GameMaterialCustomization.game_id
        WHERE GameMaterialCustomization.id = %s
          AND GameMaterialCustomization.teacher_id = %s
          AND GameMaterialCustomization.student_id = %s
        """,
        (config_id, teacher_id, student_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=400, detail="素材配置必須屬於這位學生")
    if row["game_code"] != game_code:
        raise HTTPException(status_code=400, detail="素材配置與此關卡的遊戲不一致")


def clean_workflow(cursor, teacher_id: int, student_id: int, body: WorkflowIn) -> dict:
    """整理選線前開場、故事線與每步閉場。"""
    if not body.storylines:
        raise HTTPException(status_code=400, detail="至少要有一條故事線")
    require_consecutive_orders([item.order for item in body.storylines])
    storylines: list[dict[str, object]] = []
    for line in sorted(body.storylines, key=lambda item: item.order):
        name = line.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="故事線名稱不能是空白")
        if not line.steps:
            raise HTTPException(status_code=400, detail="每條故事線至少要有一步")
        require_consecutive_orders([step.order for step in line.steps])
        steps: list[dict[str, object]] = []
        for step in sorted(line.steps, key=lambda item: item.order):
            if step.game not in KNOWN_GAMES:
                raise HTTPException(status_code=400, detail="關卡必須使用現有的遊戲")
            if step.gameMaterialCustomizationId is not None:
                require_student_material(
                    cursor,
                    teacher_id,
                    student_id,
                    step.game,
                    step.gameMaterialCustomizationId,
                )
            steps.append(
                {
                    "game": step.game,
                    "gameMaterialCustomizationId": step.gameMaterialCustomizationId,
                    "order": step.order,
                    "endNpcName": step.endNpcName.strip(),
                    "endDialogues": clean_dialogue_lines(step.endDialogues),
                }
            )
        storylines.append({"name": name, "order": line.order, "steps": steps})
    return {
        "startNpcName": body.startNpcName.strip(),
        "startDialogues": clean_dialogue_lines(body.startDialogues),
        "storylines": storylines,
    }


@router.get("/workflow/default")
def get_workflow_default(_teacher_id: int = Depends(current_teacher_id)) -> dict:
    """回傳全站預設關卡 JSON。未登入時 Depends 回傳 401。"""
    return load_default_payload()


def load_student_workflow(student_id: int) -> dict:
    """依學生 id 讀自訂關卡。沒有列或缺檔時回傳 Default。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id FROM Student WHERE id = %s",
                (student_id,),
            )
            student = cursor.fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="找不到這位學生")
            cursor.execute(
                """
                SELECT json_path
                FROM GameWorkflowCustomization
                WHERE teacher_id = %s AND student_id = %s
                LIMIT 1
                """,
                (student["teacher_id"], student_id),
            )
            row = cursor.fetchone()

    if row:
        path = storage_file(row["json_path"])
        if path.is_file():
            return parse_json_file(path)
    return load_default_payload()


@router.get("/students/{student_id}/workflow")
def get_student_workflow(
    student_id: int, teacher_id: int = Depends(current_teacher_id)
) -> dict:
    """有自訂檔時回傳自訂檔。沒有列或缺檔時回傳 Default。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            get_owned_student(cursor, teacher_id, student_id)
    return load_student_workflow(student_id)


@router.put("/students/{student_id}/workflow")
def put_student_workflow(
    student_id: int,
    body: WorkflowIn,
    teacher_id: int = Depends(current_teacher_id),
) -> dict:
    """整份覆寫此學生的故事線。已有路徑列時更新該列。沒有路徑列時插入一列。"""
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            student = get_owned_student(cursor, teacher_id, student_id)
            teacher = get_teacher(cursor, teacher_id)
            payload = clean_workflow(cursor, teacher_id, student_id, body)
            relative = workflow_custom_path(teacher["username"], student["username"])
            path = storage_file(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            cursor.execute(
                "SELECT id FROM GameWorkflowCustomization WHERE teacher_id = %s AND student_id = %s LIMIT 1",
                (teacher_id, student_id),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE GameWorkflowCustomization SET json_path = %s WHERE id = %s",
                    (relative, existing["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO GameWorkflowCustomization (teacher_id, student_id, json_path)
                    VALUES (%s, %s, %s)
                    """,
                    (teacher_id, student_id, relative),
                )
    return payload
