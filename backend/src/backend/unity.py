"""Unity 區網 API。健康檢查、學生故事線整包與單筆素材。"""

import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.database import db_conn
from backend.material import (
    assemble_play,
    flat_customization_id,
    load_default_payload,
    load_owned_material_config,
    load_student_payload_for_unity,
)
from backend.workflow import load_student_workflow

router = APIRouter(prefix="/api/unity", tags=["unity"])


def require_unity_key(x_unity_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("UNITY_API_KEY", "")
    provided = x_unity_key or ""
    if (
        not expected
        or len(provided) != len(expected)
        or not hmac.compare_digest(provided, expected)
    ):
        raise HTTPException(status_code=401, detail="無效的 Unity 識別碼")


def student_username(student_id: int) -> str:
    """依學生 id 讀帳號。找不到回 404。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT username FROM Student WHERE id = %s",
                (student_id,),
            )
            student = cursor.fetchone()
    if student is None:
        raise HTTPException(status_code=404, detail="找不到這位學生")
    return student["username"]


def playable_step(
    student_id: int, student_name: str, step: dict, config_id: int | None
) -> dict:
    """為一個步驟附上可玩的 material。id 為空時用該遊戲 Default。"""
    game_code = step.get("game")
    if not isinstance(game_code, str) or not game_code:
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    end_name = step.get("endNpcName")
    if not isinstance(end_name, str):
        end_name = ""
    dialogues = step.get("endDialogues")
    if not isinstance(dialogues, list):
        dialogues = []
    if config_id is None:
        config = load_default_payload(game_code)
    else:
        _owner, config = load_owned_material_config(student_id, config_id)
        if config.get("game") != game_code:
            raise HTTPException(status_code=500, detail="設定檔格式不對")
    return {
        "game": game_code,
        "gameMaterialCustomizationId": config_id,
        "order": step.get("order"),
        "endNpcName": end_name,
        "endDialogues": dialogues,
        "material": assemble_play(student_name, config),
    }


def pack_storylines(student_id: int, student_name: str, raw: dict) -> dict:
    """照故事線存檔組 material。有 id 讀該筆。null 讀該遊戲 Default。"""
    storylines = raw.get("storylines")
    if not isinstance(storylines, list):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    packed_lines = []
    for line in storylines:
        if not isinstance(line, dict) or not isinstance(line.get("steps"), list):
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        packed_steps = []
        for step in line["steps"]:
            if not isinstance(step, dict):
                raise HTTPException(status_code=500, detail="設定檔格式不對")
            config_id = step.get("gameMaterialCustomizationId")
            if isinstance(config_id, bool) or not isinstance(config_id, (int, type(None))):
                raise HTTPException(status_code=500, detail="設定檔格式不對")
            packed_steps.append(playable_step(student_id, student_name, step, config_id))
        name = line.get("name")
        if not isinstance(name, str):
            name = ""
        packed_lines.append({"name": name, "order": line.get("order"), "steps": packed_steps})
    start_name = raw.get("startNpcName")
    if not isinstance(start_name, str):
        start_name = ""
    start_lines = raw.get("startDialogues")
    if not isinstance(start_lines, list):
        start_lines = []
    return {
        "startNpcName": start_name,
        "startDialogues": start_lines,
        "storylines": packed_lines,
    }


def pack_legacy_games(student_id: int, student_name: str, raw: dict) -> dict:
    """把舊的 games 編成一條名稱為預設的故事線。選線前開場留空。只在正好一筆扁平舊檔時綁定該列。"""
    games = raw.get("games")
    if not isinstance(games, list):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    steps = []
    for step in games:
        if not isinstance(step, dict):
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        game_code = step.get("game")
        if not isinstance(game_code, str):
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        steps.append(
            playable_step(
                student_id,
                student_name,
                step,
                flat_customization_id(student_id, game_code),
            )
        )
    return {
        "startNpcName": "",
        "startDialogues": [],
        "storylines": [{"name": "預設", "order": 1, "steps": steps}],
    }


def pack_workflow(student_id: int, student_name: str, raw: dict) -> dict:
    """存檔已是故事線時照檔附上 material。舊的 games 編成一條預設故事線。這次組裝不寫回磁碟。"""
    if isinstance(raw.get("storylines"), list):
        return pack_storylines(student_id, student_name, raw)
    if isinstance(raw.get("games"), list):
        return pack_legacy_games(student_id, student_name, raw)
    raise HTTPException(status_code=500, detail="設定檔格式不對")


@router.get("/health")
def unity_health(_auth: None = Depends(require_unity_key)) -> dict[str, str]:
    return {"status": "ok"}


@router.get("/students/{student_id}")
def unity_student_pack(
    student_id: int, _auth: None = Depends(require_unity_key)
) -> dict:
    """回傳學生名稱與故事線。每個步驟附上 material。"""
    workflow = load_student_workflow(student_id)
    student_name = student_username(student_id)
    return {
        "studentName": student_name,
        "workflow": pack_workflow(student_id, student_name, workflow),
    }


@router.get("/students/{student_id}/material-configs/{config_id}")
def unity_material_config(
    student_id: int, config_id: int, _auth: None = Depends(require_unity_key)
) -> dict:
    """回傳這位學生的一筆可玩素材。找不到回 404。"""
    student_name, config = load_owned_material_config(student_id, config_id)
    return assemble_play(student_name, config)


@router.get("/students/{student_id}/games/{game_code}")
def unity_student_game(
    student_id: int, game_code: str, _auth: None = Depends(require_unity_key)
) -> dict:
    """沒有自訂列時回 Default。正好一筆扁平舊檔且檔案存在時回那一筆。檔案不在時回 Default。其餘回 400。"""
    student_name, config = load_student_payload_for_unity(student_id, game_code)
    return assemble_play(student_name, config)
