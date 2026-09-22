"""storage/ 的路徑與 JSON。關卡與素材用同一套讀檔與刪檔規則。"""

import json
import re
from pathlib import Path

from fastapi import HTTPException

from backend.database import STORAGE_DIR

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def require_safe_name(name: str) -> str:
    if not SAFE_NAME.match(name):
        raise HTTPException(status_code=500, detail=f"名稱不可用於路徑：{name}")
    return name


def storage_file(relative_path: str) -> Path:
    """把資料庫的相對 json_path 接到 storage/。拒絕跳出此目錄的路徑。"""
    cleaned = relative_path.replace("\\", "/").lstrip("/")
    root = STORAGE_DIR.resolve()
    resolved = (root / cleaned).resolve()
    if not resolved.is_relative_to(root):
        raise HTTPException(status_code=400, detail="設定檔路徑不合法")
    return resolved


def parse_json_file(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail=f"設定檔讀取失敗：{error}") from error
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    return payload


def read_json_file(relative_path: str, missing_detail: str) -> dict:
    path = storage_file(relative_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=missing_detail)
    return parse_json_file(path)


def clean_dialogue_lines(lines: list[str]) -> list[str]:
    """去掉前後空白。不儲存空行。"""
    cleaned: list[str] = []
    for line in lines:
        text = line.strip()
        if text:
            cleaned.append(text)
    return cleaned


def remove_empty_parents(start: Path, stop: Path) -> None:
    current = start
    while current != stop and current.is_dir() and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


def delete_custom_student_json(
    customization: str, teacher_username: str, student_username: str
) -> None:
    """刪除學生時，刪除該生目錄底下全部 JSON，含子目錄。名稱不合法則略過。"""
    if (
        not SAFE_NAME.match(customization)
        or not SAFE_NAME.match(teacher_username)
        or not SAFE_NAME.match(student_username)
    ):
        return
    kind_root = (STORAGE_DIR / customization).resolve()
    student_dir = (kind_root / teacher_username / student_username).resolve()
    if not student_dir.is_relative_to(kind_root) or not student_dir.is_dir():
        return
    json_files = [path for path in student_dir.rglob("*.json") if path.is_file()]
    for path in json_files:
        path.unlink(missing_ok=True)
    directories = [path for path in student_dir.rglob("*") if path.is_dir()]
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    remove_empty_parents(student_dir, kind_root)
