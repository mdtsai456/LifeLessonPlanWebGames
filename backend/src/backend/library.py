"""素材庫 API。回傳一款遊戲的分類，以及分類下的素材。

分類（Tag）是選遊戲後的 tab。
素材（Material）是分類下的卡片，含名稱與圖。

所有老師共用同一份素材庫。
新增的分類不跨遊戲共用。
種子分類不修改。
"""

import html
from pathlib import Path

import pymysql
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.auth import current_teacher_id
from backend.database import STATIC_DIR, db_conn

router = APIRouter(prefix="/api", tags=["library"])

MATERIAL_DIR = STATIC_DIR / "GameMaterial" / "Shared"
ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
# 與 frontend/js/state.js THEME_COLORS 相同。
PLACEHOLDER_COLORS = ["#3d8b5c", "#2f7fd1", "#d45b8c", "#e07a2f", "#8b6914", "#4f7d8c", "#7a4bd4"]


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class MaterialRename(BaseModel):
    name: str = Field(min_length=1, max_length=150)


def get_game(cursor, game_code: str) -> dict:
    cursor.execute("SELECT id, game_code, game_name FROM Game WHERE game_code = %s", (game_code,))
    game = cursor.fetchone()
    if game is None:
        raise HTTPException(status_code=404, detail=f"找不到遊戲「{game_code}」")
    return game


def get_tag(cursor, tag_code: str) -> dict:
    cursor.execute("SELECT id, tag_code, tag_name FROM Tag WHERE tag_code = %s", (tag_code,))
    tag = cursor.fetchone()
    if tag is None:
        raise HTTPException(status_code=404, detail=f"找不到分類「{tag_code}」")
    return tag


def get_material(cursor, material_code: str) -> dict:
    cursor.execute(
        """
        SELECT id, material_code, material_name, file_path
        FROM GameMaterial
        WHERE material_code = %s
        """,
        (material_code,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"找不到素材「{material_code}」")
    return row


def image_url(file_path: str) -> str:
    """回傳前端使用的靜態路徑。

    檔案存在時接上 ?v= 與 st_mtime_ns。
    檔案不存在時不加版本。
    例如 /static/GameMaterial/Shared/MAT001.png?v=1710000000000000000。
    """
    relative = file_path.replace("\\", "/")
    url = f"/static/{relative}"
    path = STATIC_DIR / relative
    if not path.is_file():
        return url
    return f"{url}?v={path.stat().st_mtime_ns}"


def write_placeholder(material_code: str, name: str, tag_code: str) -> str:
    """未上傳圖時寫入首字色塊。file_path 不可為空。"""
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    label = html.escape(name.strip()[:1] or "?", quote=True)
    color = PLACEHOLDER_COLORS[sum(ord(ch) for ch in tag_code) % len(PLACEHOLDER_COLORS)]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
        f'<rect width="256" height="256" rx="36" fill="{color}"/>'
        f'<text x="128" y="150" text-anchor="middle" font-size="72" fill="#ffffff" '
        f'font-family="Segoe UI, sans-serif">{label}</text></svg>'
    )
    relative = f"GameMaterial/Shared/{material_code}.svg"
    (STATIC_DIR / relative).write_text(svg, encoding="utf-8")
    return relative


def save_upload(material_code: str, upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIX:
        raise HTTPException(status_code=400, detail="圖片格式請用 png、jpg、gif、webp 或 svg")
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="圖片是空的")
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="圖片請小於 5MB")
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    relative = f"GameMaterial/Shared/{material_code}{suffix}"
    (STATIC_DIR / relative).write_bytes(data)
    return relative


def delete_material_file(file_path: str) -> None:
    path = (STATIC_DIR / file_path).resolve()
    if path.is_relative_to(STATIC_DIR.resolve()) and path.exists():
        path.unlink()


def next_material_code(cursor) -> str:
    """以現存最大 MAT 數字加 1 產生代碼。此代碼不是資料表 id。刪除列之後，此代碼與資料表 id 不相同。"""
    cursor.execute(
        """
        SELECT MAX(CAST(SUBSTRING(material_code, 4) AS UNSIGNED)) AS n
        FROM GameMaterial
        WHERE material_code REGEXP '^MAT[0-9]+$'
        """
    )
    row = cursor.fetchone()
    return f"MAT{int(row['n'] or 0) + 1:03d}"


def next_tag_code(cursor) -> str:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM Tag")
    return f"TAG{int(cursor.fetchone()['n']):03d}"


def is_glb(file_path: str) -> bool:
    return Path(file_path).suffix.lower() == ".glb"


def serialize_material(row: dict) -> dict:
    url = image_url(row["file_path"])
    payload = {"code": row["material_code"], "name": row["material_name"]}
    if is_glb(row["file_path"]):
        payload["model_url"] = url
    else:
        payload["image_url"] = url
    return payload


def list_tags_for_game(cursor, game_code: str) -> list[dict[str, str]]:
    """讀取這款遊戲的分類。預算模式沒有分類時改讀超市購物。"""
    game = get_game(cursor, game_code)
    cursor.execute(
        """
        SELECT t.tag_code AS code, t.tag_name AS name
        FROM GameTag gt
        JOIN Tag t ON t.id = gt.tag_id
        WHERE gt.game_id = %s
        ORDER BY t.id
        """,
        (game["id"],),
    )
    tags = cursor.fetchall()
    if not tags and game_code == "MarketShoppingBudgetMode":
        return list_tags_for_game(cursor, "MarketShopping")
    return tags


def move_temp_file(material_code: str, temp_id: str) -> str:
    """把 generate 寫入的暫存檔移到 Shared。temp_id 只能是檔名。不可含路徑。"""
    if not temp_id or any(ch in temp_id for ch in ("/", "\\", ".")):
        raise HTTPException(status_code=400, detail="預覽已過期，請重新生成")
    tmp_dir = STATIC_DIR / "GameMaterial" / "tmp"
    png = tmp_dir / f"{temp_id}.png"
    glb = tmp_dir / f"{temp_id}.glb"
    source = png if png.is_file() else glb if glb.is_file() else None
    if source is None:
        raise HTTPException(status_code=400, detail="預覽已過期，請重新生成")
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    relative = f"GameMaterial/Shared/{material_code}{source.suffix.lower()}"
    source.replace(STATIC_DIR / relative)
    return relative


@router.get("/games")
def list_games(_teacher_id: int = Depends(current_teacher_id)) -> list[dict[str, str]]:
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT game_code AS code, game_name AS name FROM Game ORDER BY id")
            return cursor.fetchall()


@router.get("/games/{game_code}/tags")
def list_game_tags(
    game_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> list[dict[str, str]]:
    """讀取 GameTag。回傳這款遊戲可用的分類。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            return list_tags_for_game(cursor, game_code)


@router.get("/games/{game_code}/library")
def list_game_library(
    game_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> list[dict[str, object]]:
    """一款遊戲的全部分類與素材。給配置頁一次載入。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            tags = list_tags_for_game(cursor, game_code)
            library: list[dict[str, object]] = []
            for tag in tags:
                cursor.execute(
                    """
                    SELECT gm.material_code, gm.material_name, gm.file_path
                    FROM GameMaterialTag gmt
                    JOIN GameMaterial gm ON gm.id = gmt.game_material_id
                    JOIN Tag t ON t.id = gmt.tag_id
                    WHERE t.tag_code = %s
                    ORDER BY gm.id
                    """,
                    (tag["code"],),
                )
                library.append(
                    {
                        "code": tag["code"],
                        "name": tag["name"],
                        "materials": [serialize_material(row) for row in cursor.fetchall()],
                    }
                )
            return library


@router.post("/games/{game_code}/tags", status_code=201)
def add_game_tag(
    game_code: str, payload: TagCreate, _teacher_id: int = Depends(current_teacher_id)
) -> dict[str, object]:
    """若這款遊戲沒有此分類名稱，則新建一筆 Tag。

    即使其他遊戲已有同名分類，也不共用該 Tag。
    之後新增的素材不會出現在其他遊戲。
    """
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="請輸入分類名稱")

    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            game = get_game(cursor, game_code)
            cursor.execute(
                """
                SELECT t.id
                FROM GameTag gt
                JOIN Tag t ON t.id = gt.tag_id
                WHERE gt.game_id = %s AND t.tag_name = %s
                """,
                (game["id"], name),
            )
            if cursor.fetchone() is not None:
                raise HTTPException(status_code=409, detail=f"這個遊戲已經有分類「{name}」")

            code = next_tag_code(cursor)
            cursor.execute(
                "INSERT INTO Tag (tag_code, tag_name) VALUES (%s, %s)",
                (code, name),
            )
            tag_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO GameTag (game_id, tag_id) VALUES (%s, %s)",
                (game["id"], tag_id),
            )
            return {"code": code, "name": name, "created_tag": True}


@router.delete("/games/{game_code}/tags/{tag_code}")
def remove_game_tag(
    game_code: str, tag_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> dict[str, str]:
    """只刪除這款遊戲與分類的關聯。其他遊戲的 GameTag 不修改。"""
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            game = get_game(cursor, game_code)
            tag = get_tag(cursor, tag_code)
            cursor.execute(
                "DELETE FROM GameTag WHERE game_id = %s AND tag_id = %s",
                (game["id"], tag["id"]),
            )
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"這個遊戲沒有分類「{tag_code}」",
                )
            cursor.execute("SELECT 1 FROM GameTag WHERE tag_id = %s LIMIT 1", (tag["id"],))
            still_used = cursor.fetchone() is not None
            cursor.execute("SELECT 1 FROM GameMaterialTag WHERE tag_id = %s LIMIT 1", (tag["id"],))
            has_materials = cursor.fetchone() is not None
            # 沒有遊戲使用此 Tag，且沒有素材時，才刪除 Tag。未使用的測試分類不保留。
            if not still_used and not has_materials:
                cursor.execute("DELETE FROM Tag WHERE id = %s", (tag["id"],))
            return {"status": "deleted"}


@router.get("/tags/{tag_code}/materials")
def list_tag_materials(
    tag_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> dict[str, object]:
    """讀取 GameMaterialTag。回傳此分類下的素材。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            tag = get_tag(cursor, tag_code)
            cursor.execute(
                """
                SELECT gm.material_code, gm.material_name, gm.file_path
                FROM GameMaterialTag gmt
                JOIN GameMaterial gm ON gm.id = gmt.game_material_id
                WHERE gmt.tag_id = %s
                ORDER BY gm.id
                """,
                (tag["id"],),
            )
            materials = [serialize_material(row) for row in cursor.fetchall()]
            return {"code": tag["tag_code"], "name": tag["tag_name"], "materials": materials}


@router.post("/tags/{tag_code}/materials", status_code=201)
def add_tag_material(
    tag_code: str,
    name: str = Form(...),
    image: UploadFile | None = File(None),
    temp_id: str | None = Form(None),
    _teacher_id: int = Depends(current_teacher_id),
) -> dict[str, str]:
    material_name = name.strip()
    if not material_name:
        raise HTTPException(status_code=400, detail="請輸入素材名稱")

    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            tag = get_tag(cursor, tag_code)
            code = next_material_code(cursor)
            raw_temp = (temp_id or "").strip()
            if raw_temp:
                file_path = move_temp_file(code, raw_temp)
            elif image is not None and image.filename:
                file_path = save_upload(code, image)
            else:
                file_path = write_placeholder(code, material_name, tag_code)
            try:
                cursor.execute(
                    """
                    INSERT INTO GameMaterial (material_code, material_name, file_path)
                    VALUES (%s, %s, %s)
                    """,
                    (code, material_name, file_path),
                )
                material_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO GameMaterialTag (game_material_id, tag_id) VALUES (%s, %s)",
                    (material_id, tag["id"]),
                )
            except pymysql.Error as error:
                delete_material_file(file_path)
                raise HTTPException(status_code=500, detail=f"資料庫寫入失敗：{error}") from error
            return serialize_material(
                {"material_code": code, "material_name": material_name, "file_path": file_path}
            )


@router.patch("/materials/{material_code}")
def rename_material(
    material_code: str, payload: MaterialRename, _teacher_id: int = Depends(current_teacher_id)
) -> dict[str, str]:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="請輸入素材名稱")
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            row = get_material(cursor, material_code)
            # MySQL 更新成相同值時 rowcount 可能是 0。不可用 rowcount 判斷列是否存在。
            if row["material_name"] != name:
                cursor.execute(
                    "UPDATE GameMaterial SET material_name = %s WHERE material_code = %s",
                    (name, material_code),
                )
                row["material_name"] = name
            return serialize_material(row)


@router.put("/materials/{material_code}/image")
def replace_material_image(
    material_code: str,
    image: UploadFile = File(...),
    _teacher_id: int = Depends(current_teacher_id),
) -> dict[str, str]:
    old_path = None
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            material = get_material(cursor, material_code)
            if is_glb(material["file_path"]):
                raise HTTPException(status_code=400, detail="3D 素材不可更換圖片")
            new_path = save_upload(material_code, image)
            old_path = material["file_path"]
            cursor.execute(
                "UPDATE GameMaterial SET file_path = %s WHERE id = %s",
                (new_path, material["id"]),
            )
            material["file_path"] = new_path
            result = serialize_material(material)
    if old_path != new_path:
        delete_material_file(old_path)
    return result


@router.delete("/tags/{tag_code}/materials/{material_code}")
def remove_tag_material(
    tag_code: str, material_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> dict[str, str]:
    """從此分類移除素材。沒有其他分類使用時，才刪除 GameMaterial 與檔案。"""
    file_to_delete = None
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            tag = get_tag(cursor, tag_code)
            material = get_material(cursor, material_code)
            cursor.execute(
                "DELETE FROM GameMaterialTag WHERE game_material_id = %s AND tag_id = %s",
                (material["id"], tag["id"]),
            )
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"分類「{tag_code}」沒有素材「{material_code}」",
                )
            cursor.execute(
                "SELECT 1 FROM GameMaterialTag WHERE game_material_id = %s LIMIT 1",
                (material["id"],),
            )
            if cursor.fetchone() is None:
                cursor.execute("DELETE FROM GameMaterial WHERE id = %s", (material["id"],))
                file_to_delete = material["file_path"]
                result = {"status": "deleted"}
            else:
                result = {"status": "unlinked"}
    if file_to_delete:
        delete_material_file(file_to_delete)
    return result
