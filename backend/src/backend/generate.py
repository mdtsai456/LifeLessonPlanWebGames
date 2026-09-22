"""2D 與 3D 生成。寫入暫存檔。不執行素材 CRUD。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import current_teacher_id
from backend.cube_generate import generate_png_to_path
from backend.database import STATIC_DIR, db_conn
from backend.gpu_job import BusyError, UnavailableError
from backend.library import get_tag
from backend.trellis_generate import generate_glb_to_path

router = APIRouter(prefix="/api", tags=["generate"])

TMP_DIR = STATIC_DIR / "GameMaterial" / "tmp"
TRELLIS_PROMPT_SUFFIX = "(low poly, with smooth curve)"


class Generate2dIn(BaseModel):
    objectName: str


class Generate3dIn(BaseModel):
    prompt: str


def with_trellis_style_suffix(prompt: str) -> str:
    """在描述後面附加風格詞。已有風格詞時不重複附加。"""
    text = prompt.strip()
    if TRELLIS_PROMPT_SUFFIX.lower() in text.lower():
        return text
    return f"{text} {TRELLIS_PROMPT_SUFFIX}"


def _http_from_generate(exc: Exception) -> HTTPException:
    if isinstance(exc, BusyError):
        return HTTPException(status_code=429, detail="正在生成中，請稍後再試")
    if isinstance(exc, UnavailableError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail=f"生成失敗：{exc}")


@router.post("/tags/{tag_code}/generate-2d")
def generate_2d(
    tag_code: str,
    payload: Generate2dIn,
    _teacher_id: int = Depends(current_teacher_id),
) -> dict[str, str]:
    object_name = payload.objectName.strip()
    if not object_name:
        raise HTTPException(status_code=422, detail="請輸入物件名稱")

    with db_conn() as connection:
        with connection.cursor() as cursor:
            get_tag(cursor, tag_code)

    temp_id = uuid.uuid4().hex
    dest = TMP_DIR / f"{temp_id}.png"
    try:
        generate_png_to_path(object_name, dest)
    except Exception as exc:
        raise _http_from_generate(exc) from exc
    return {"tempId": temp_id, "imageUrl": f"/static/GameMaterial/tmp/{temp_id}.png"}


@router.post("/tags/{tag_code}/generate-3d")
def generate_3d(
    tag_code: str,
    payload: Generate3dIn,
    _teacher_id: int = Depends(current_teacher_id),
) -> dict[str, str]:
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="請輸入生成描述")
    prompt = with_trellis_style_suffix(prompt)

    with db_conn() as connection:
        with connection.cursor() as cursor:
            get_tag(cursor, tag_code)

    temp_id = uuid.uuid4().hex
    dest = TMP_DIR / f"{temp_id}.glb"
    try:
        generate_glb_to_path(prompt, dest)
    except Exception as exc:
        raise _http_from_generate(exc) from exc
    return {"tempId": temp_id, "modelUrl": f"/static/GameMaterial/tmp/{temp_id}.glb"}
