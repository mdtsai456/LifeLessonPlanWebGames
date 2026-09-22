"""遊戲格子配置。全站使用 Default。老師可為學生的一款遊戲存多份配置。

JSON 放在 storage/。新檔寫在遊戲代號子目錄。已存在的扁平檔留在原路徑。
支援 MemoryMatch、PairVacuum、DecisionParkour、SortArena、
MarketShopping、MarketShoppingBudgetMode。
"""

import json
import math
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import current_teacher_id, get_teacher
from backend.database import db_conn
from backend.library import get_game, get_material, get_tag, image_url
from backend.storage import (
    clean_dialogue_lines,
    parse_json_file,
    read_json_file,
    require_safe_name,
    storage_file,
)
from backend.students import get_owned_student

router = APIRouter(prefix="/api", tags=["material"])

THEME_KEYS = ("theme_1", "theme_2", "theme_3", "theme_4")
DISTRACTOR_KEYS = (
    "distractor_1",
    "distractor_2",
    "distractor_3",
    "distractor_4",
    "distractor_5",
)
SLOT_KEYS = THEME_KEYS + DISTRACTOR_KEYS
VACUUM_KEYS = ("slot_1", "slot_2", "slot_3", "slot_4", "slot_5")
PARKOUR_THEME_KEYS = tuple(f"theme_{index}" for index in range(1, 7))
PARKOUR_DISTRACTOR_KEYS = tuple(f"distractor_{index}" for index in range(1, 13))
PARKOUR_KEYS = PARKOUR_THEME_KEYS + PARKOUR_DISTRACTOR_KEYS
SORT_KEYS = tuple(
    f"bin_{bin_index}_{slot_index}"
    for bin_index in range(1, 5)
    for slot_index in range(1, 6)
)
MARKET_SHELF_GROUPS = (
    ("shelf_regular", 21),
    ("shelf_veg", 4),
    ("shelf_fruit", 8),
    ("shelf_meat", 4),
    ("shelf_milk", 1),
    ("shelf_rice", 2),
)
MARKET_SLOT_KEYS = tuple(
    f"{prefix}_{index}"
    for prefix, count in MARKET_SHELF_GROUPS
    for index in range(1, count + 1)
)
MARKET_GAMES = {"MarketShopping", "MarketShoppingBudgetMode"}
MATERIAL_CODE_RE = re.compile(r"(MAT[0-9]+)", re.IGNORECASE)


class GameMaterialIn(BaseModel):
    game: str
    tag: str = ""
    tags: list[str] = Field(default_factory=list)
    items: dict[str, str]
    basketOrder: list[str] = Field(default_factory=list)
    budget: float | None = None
    prices: dict[str, float] = Field(default_factory=dict)
    Start_NPC_Name: str = ""
    Start_Dialogues: list[str] = Field(default_factory=list)


def require_supported_game(game_code: str) -> None:
    if game_code not in SUPPORTED_GAMES:
        raise HTTPException(status_code=400, detail="此遊戲配置尚未提供")


def customization_json_path(
    teacher_username: str, student_username: str, game_code: str, config_id: int
) -> str:
    """路徑由後端產生。不接受 client 指定的路徑。"""
    teacher_username = require_safe_name(teacher_username)
    student_username = require_safe_name(student_username)
    game_code = require_safe_name(game_code)
    return (
        f"GameMaterialCustomization/{teacher_username}/{student_username}/"
        f"{game_code}/{config_id}.json"
    )


def is_flat_material_path(json_path: str, game_code: str) -> bool:
    """扁平舊檔的路徑以 /遊戲代號.json 結尾。"""
    normalized = json_path.replace("\\", "/").rstrip("/")
    return normalized.endswith(f"/{game_code}.json")


def attach_material_identity(payload: dict, config_id: int, json_path: str) -> dict:
    """在回傳內容加上 id 與 json_path。磁碟檔不含這兩個欄位。"""
    body = dict(payload)
    body["id"] = config_id
    body["json_path"] = json_path
    return body


def read_custom_material(config_id: int, json_path: str) -> dict:
    """讀一筆自訂檔。格子轉成 /static/ 路徑。"""
    path = storage_file(json_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="找不到素材設定檔")
    payload = public_items_payload(parse_json_file(path))
    return attach_material_identity(payload, config_id, json_path)


def load_default_payload(game_code: str) -> dict:
    require_supported_game(game_code)
    with db_conn() as connection:
        with connection.cursor() as cursor:
            game = get_game(cursor, game_code)
            cursor.execute(
                "SELECT json_path FROM GameMaterialDefault WHERE game_id = %s",
                (game["id"],),
            )
            row = cursor.fetchone()
    relative = row["json_path"] if row else f"GameMaterialDefault/{game_code}.json"
    return public_items_payload(read_json_file(relative, "找不到預設素材配置"))


def load_student_payload_for_unity(student_id: int, game_code: str) -> tuple[str, dict]:
    """沒有自訂列時回 Default。正好一筆扁平舊檔且檔案存在時回那一筆。檔案不在時回 Default。其餘回 400。"""
    require_supported_game(game_code)
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT username, teacher_id FROM Student WHERE id = %s",
                (student_id,),
            )
            student = cursor.fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="找不到這位學生")
            game = get_game(cursor, game_code)
            cursor.execute(
                """
                SELECT json_path
                FROM GameMaterialCustomization
                WHERE teacher_id = %s AND student_id = %s AND game_id = %s
                """,
                (student["teacher_id"], student_id, game["id"]),
            )
            rows = cursor.fetchall()
    if not rows:
        return student["username"], load_default_payload(game_code)
    if len(rows) == 1 and is_flat_material_path(rows[0]["json_path"], game_code):
        path = storage_file(rows[0]["json_path"])
        if path.is_file():
            return student["username"], public_items_payload(parse_json_file(path))
        return student["username"], load_default_payload(game_code)
    raise HTTPException(status_code=400, detail="此遊戲沒有唯一的扁平素材配置")


def load_owned_material_config(student_id: int, config_id: int) -> tuple[str, dict]:
    """讀取屬於這位學生的一筆素材。找不到或不屬於這位學生回 404。"""
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT username FROM Student WHERE id = %s",
                (student_id,),
            )
            student = cursor.fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="找不到這位學生")
            cursor.execute(
                """
                SELECT id, json_path
                FROM GameMaterialCustomization
                WHERE id = %s AND student_id = %s
                """,
                (config_id, student_id),
            )
            row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到這份素材配置")
    return student["username"], read_custom_material(row["id"], row["json_path"])


def flat_customization_id(student_id: int, game_code: str) -> int | None:
    """正好一筆且檔案存在的扁平舊列時回傳 id。沒有或多筆時回傳 None。"""
    require_supported_game(game_code)
    with db_conn() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id FROM Student WHERE id = %s",
                (student_id,),
            )
            student = cursor.fetchone()
            if student is None:
                raise HTTPException(status_code=404, detail="找不到這位學生")
            game = get_game(cursor, game_code)
            cursor.execute(
                """
                SELECT id, json_path
                FROM GameMaterialCustomization
                WHERE teacher_id = %s AND student_id = %s AND game_id = %s
                """,
                (student["teacher_id"], student_id, game["id"]),
            )
            rows = cursor.fetchall()
    flats = []
    for row in rows:
        if not is_flat_material_path(row["json_path"], game_code):
            continue
        if not storage_file(row["json_path"]).is_file():
            continue
        flats.append(row)
    if len(flats) != 1:
        return None
    return int(flats[0]["id"])


def material_code_from_item(value: str) -> str:
    """從 MAT003 或 /static/.../MAT003.svg 取出素材代碼。"""
    text = value.strip().replace("\\", "/")
    if not text:
        raise HTTPException(status_code=400, detail="找不到素材代碼")
    match = MATERIAL_CODE_RE.search(text)
    if match is None:
        raise HTTPException(status_code=400, detail=f"找不到素材「{value}」")
    return match.group(1).upper()


def items_as_static_urls(cursor, items: dict, skip_missing: bool = False) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key, value in items.items():
        try:
            material = get_material(cursor, material_code_from_item(str(value)))
            resolved[key] = image_url(material["file_path"])
        except HTTPException as error:
            if skip_missing and error.status_code in {400, 404}:
                continue
            raise
    return resolved


def public_items_payload(payload: dict) -> dict:
    """把格子轉成目前的 /static/ 路徑。舊檔的 MAT 代碼也能用。
    路徑依資料庫 file_path 產生。svg 改成 png 後，畫面與 Unity 使用新路徑。
    超市缺素材時略過該格，並從 prices 與 basketOrder 移除對應代碼。
    """
    items = payload.get("items")
    if not isinstance(items, dict):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    public = dict(payload)
    skip_missing = payload.get("game") in MARKET_GAMES
    try:
        with db_conn() as connection:
            with connection.cursor() as cursor:
                public["items"] = items_as_static_urls(cursor, items, skip_missing)
    except HTTPException as error:
        if error.status_code in {400, 404}:
            raise HTTPException(status_code=500, detail="設定檔格式不對") from error
        raise
    if skip_missing:
        present = {material_code_from_item(value) for value in public["items"].values()}
        prices = public.get("prices")
        if isinstance(prices, dict):
            public["prices"] = {
                code: amount for code, amount in prices.items() if code in present
            }
        basket = public.get("basketOrder")
        if isinstance(basket, list):
            public["basketOrder"] = [code for code in basket if code in present]
    return public


def codes_in_tag(cursor, tag_id: int) -> set[str]:
    cursor.execute(
        """
        SELECT gm.material_code
        FROM GameMaterialTag gmt
        JOIN GameMaterial gm ON gm.id = gmt.game_material_id
        WHERE gmt.tag_id = %s
        """,
        (tag_id,),
    )
    return {row["material_code"] for row in cursor.fetchall()}


def item_codes_or_400(items: dict[str, str], keys: tuple[str, ...], fill_detail: str) -> list[str]:
    if set(items.keys()) != set(keys):
        raise HTTPException(status_code=400, detail=fill_detail)
    codes: list[str] = []
    for key in keys:
        raw = items[key].strip()
        if not raw:
            raise HTTPException(status_code=400, detail=fill_detail)
        codes.append(material_code_from_item(raw))
    if len(set(codes)) != len(keys):
        raise HTTPException(status_code=400, detail="同一個素材不能出現兩次")
    return codes


def require_tag_on_game(cursor, game_code: str, tag_code: str) -> dict:
    game = get_game(cursor, game_code)
    tag = get_tag(cursor, tag_code.strip())
    cursor.execute(
        "SELECT 1 FROM GameTag WHERE game_id = %s AND tag_id = %s",
        (game["id"], tag["id"]),
    )
    if cursor.fetchone() is None:
        raise HTTPException(status_code=400, detail="這個遊戲沒有此分類")
    return tag


def npc_payload(body: GameMaterialIn) -> dict[str, object]:
    return {
        "Start_NPC_Name": body.Start_NPC_Name.strip(),
        "Start_Dialogues": clean_dialogue_lines(body.Start_Dialogues),
    }


def clean_theme_slots(
    cursor,
    game_code: str,
    body: GameMaterialIn,
    all_keys: tuple[str, ...],
    theme_keys: tuple[str, ...],
    distractor_keys: tuple[str, ...],
    fill_detail: str,
) -> dict[str, object]:
    """格子必須填滿。主題格來自選定主題。干擾鍵為空時，全部格子當主題格。"""
    codes = item_codes_or_400(body.items, all_keys, fill_detail)
    tag = require_tag_on_game(cursor, game_code, body.tag)
    in_theme = codes_in_tag(cursor, tag["id"])
    items: dict[str, str] = {}
    for key, code in zip(all_keys, codes, strict=True):
        material = get_material(cursor, code)
        if key in theme_keys and code not in in_theme:
            raise HTTPException(status_code=400, detail="正確格必須來自選定主題")
        if key in distractor_keys and code in in_theme:
            raise HTTPException(status_code=400, detail="錯誤格不能放選定主題的素材")
        items[key] = image_url(material["file_path"])
    return {
        "game": game_code,
        "tag": tag["tag_code"],
        "items": items,
        **npc_payload(body),
    }


def clean_sort_arena(cursor, game_code: str, body: GameMaterialIn) -> dict[str, object]:
    """20 格必須填滿。四個主題有序。每個桶的格子必須來自對應主題。素材不可重複。"""
    stripped = [item.strip() for item in body.tags]
    if len(stripped) != 4 or len(set(stripped)) != 4 or not all(stripped):
        raise HTTPException(status_code=400, detail="請選擇剛好 4 個主題")
    codes = item_codes_or_400(body.items, SORT_KEYS, "必須正好填滿 20 個格子")
    tags = [require_tag_on_game(cursor, game_code, tag_code) for tag_code in stripped]
    theme_codes = [codes_in_tag(cursor, tag["id"]) for tag in tags]
    items: dict[str, str] = {}
    for key, code in zip(SORT_KEYS, codes, strict=True):
        material = get_material(cursor, code)
        bin_index = int(key.split("_")[1])
        if code not in theme_codes[bin_index - 1]:
            raise HTTPException(status_code=400, detail="這個格子只能放對應主題的素材")
        items[key] = image_url(material["file_path"])
    return {
        "game": game_code,
        "tags": [tag["tag_code"] for tag in tags],
        "items": items,
        **npc_payload(body),
    }


def is_valid_price(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value >= 0


def is_positive_budget(value: object) -> bool:
    return is_valid_price(value) and value > 0


def normalize_money(value: float | int) -> int | float:
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def clean_market_items(cursor, items: dict[str, str]) -> tuple[dict[str, str], set[str]]:
    cleaned: dict[str, str] = {}
    codes: set[str] = set()
    for key, value in items.items():
        if key not in MARKET_SLOT_KEYS:
            raise HTTPException(status_code=400, detail="貨架格子不合法")
        raw = value.strip()
        if not raw:
            continue
        code = material_code_from_item(raw)
        material = get_material(cursor, code)
        cleaned[key] = image_url(material["file_path"])
        codes.add(code)
    if not cleaned:
        raise HTTPException(status_code=400, detail="至少要放一件商品")
    return cleaned, codes


def clean_market_prices(raw_prices: dict[str, float], codes: set[str]) -> dict[str, int | float]:
    indexed = {key.strip().upper(): value for key, value in raw_prices.items()}
    cleaned: dict[str, int | float] = {}
    for code in codes:
        if code not in indexed:
            raise HTTPException(status_code=400, detail="每個已上架商品都要有價格")
        value = indexed[code]
        if not is_valid_price(value):
            raise HTTPException(status_code=400, detail="每個已上架商品都要有價格")
        cleaned[code] = normalize_money(value)
    return cleaned


def clean_basket_order(raw: list[str], shelf_codes: set[str]) -> list[str]:
    codes: list[str] = []
    for item in raw:
        text = item.strip()
        if not text:
            continue
        code = material_code_from_item(text)
        if code not in shelf_codes:
            raise HTTPException(status_code=400, detail="購物清單只能放貨架上的商品")
        codes.append(code)
    if not codes:
        raise HTTPException(status_code=400, detail="購物清單不能是空的")
    return codes


def clean_market_shopping(cursor, game_code: str, body: GameMaterialIn) -> dict[str, object]:
    """稀疏貨架。至少一格。允許同一商品多格。清單代碼必須仍在貨架上。"""
    items, codes = clean_market_items(cursor, body.items)
    prices = clean_market_prices(body.prices, codes)
    return {
        "game": game_code,
        "items": items,
        "basketOrder": clean_basket_order(body.basketOrder, codes),
        "prices": prices,
        **npc_payload(body),
    }


def clean_market_budget(cursor, game_code: str, body: GameMaterialIn) -> dict[str, object]:
    """稀疏貨架。至少一格。允許同一商品多格。預算必須大於 0。"""
    items, codes = clean_market_items(cursor, body.items)
    prices = clean_market_prices(body.prices, codes)
    if not is_positive_budget(body.budget):
        raise HTTPException(status_code=400, detail="預算必須大於 0")
    return {
        "game": game_code,
        "items": items,
        "budget": normalize_money(body.budget),
        "prices": prices,
        **npc_payload(body),
    }


THEME_SLOT_GAMES = {
    "MemoryMatch": (SLOT_KEYS, THEME_KEYS, DISTRACTOR_KEYS, "必須正好填滿 9 個格子"),
    "PairVacuum": (VACUUM_KEYS, VACUUM_KEYS, (), "必須正好填滿 5 個格子"),
    "DecisionParkour": (
        PARKOUR_KEYS,
        PARKOUR_THEME_KEYS,
        PARKOUR_DISTRACTOR_KEYS,
        "必須正好填滿 18 個格子",
    ),
}
CLEANERS = {
    "SortArena": clean_sort_arena,
    "MarketShopping": clean_market_shopping,
    "MarketShoppingBudgetMode": clean_market_budget,
}
SUPPORTED_GAMES = set(THEME_SLOT_GAMES) | set(CLEANERS)


def clean_game_material(cursor, game_code: str, body: GameMaterialIn) -> dict[str, object]:
    require_supported_game(game_code)
    if body.game != game_code:
        raise HTTPException(status_code=400, detail="遊戲代碼不一致")
    spec = THEME_SLOT_GAMES.get(game_code)
    if spec is not None:
        return clean_theme_slots(cursor, game_code, body, *spec)
    return CLEANERS[game_code](cursor, game_code, body)


def unity_item(cursor, raw: object) -> dict[str, str]:
    if not isinstance(raw, str) or not raw:
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    try:
        code = material_code_from_item(raw)
    except HTTPException as error:
        raise HTTPException(status_code=500, detail="設定檔格式不對") from error
    material = get_material(cursor, code)
    return {
        "code": material["material_code"],
        "name": material["material_name"],
        "imageUrl": image_url(material["file_path"]),
    }


def unity_slots(cursor, items: dict, keys: tuple[str, ...]) -> dict[str, dict[str, str]]:
    slots: dict[str, dict[str, str]] = {}
    for key in keys:
        slots[key] = unity_item(cursor, items.get(key))
    return slots


def assemble_market_play(
    cursor, student_name: str, game_code: str, config: dict, items: dict, npc: dict
) -> dict:
    raw_prices = config.get("prices")
    if not isinstance(raw_prices, dict):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    prices = {str(key).strip().upper(): value for key, value in raw_prices.items()}
    shelves: list[dict[str, object]] = []
    for slot in MARKET_SLOT_KEYS:
        raw = items.get(slot)
        if not raw:
            continue
        item = unity_item(cursor, raw)
        price = prices.get(item["code"])
        if not is_valid_price(price):
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        shelves.append(
            {
                "slot": slot,
                "code": item["code"],
                "name": item["name"],
                "imageUrl": item["imageUrl"],
                "price": normalize_money(price),
            }
        )
    if not shelves:
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    payload: dict[str, object] = {
        "game": game_code,
        "studentName": student_name,
        "shelves": shelves,
        **npc,
    }
    if game_code == "MarketShopping":
        basket_raw = config.get("basketOrder")
        if not isinstance(basket_raw, list) or not basket_raw:
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        by_code = {row["code"]: row for row in shelves}
        basket: list[dict[str, object]] = []
        for raw_code in basket_raw:
            if not isinstance(raw_code, str) or not raw_code.strip():
                raise HTTPException(status_code=500, detail="設定檔格式不對")
            try:
                code = material_code_from_item(raw_code)
            except HTTPException as error:
                raise HTTPException(status_code=500, detail="設定檔格式不對") from error
            source = by_code.get(code)
            if source is None:
                raise HTTPException(status_code=500, detail="設定檔格式不對")
            basket.append(
                {
                    "code": source["code"],
                    "name": source["name"],
                    "imageUrl": source["imageUrl"],
                    "price": source["price"],
                }
            )
        payload["basketOrder"] = basket
        return payload
    if game_code == "MarketShoppingBudgetMode":
        budget = config.get("budget")
        if not is_positive_budget(budget):
            raise HTTPException(status_code=500, detail="設定檔格式不對")
        payload["budget"] = normalize_money(budget)
        return payload
    raise HTTPException(status_code=500, detail="設定檔格式不對")


def assemble_play(student_name: str, config: dict) -> dict:
    """把存檔組成 Unity 可玩 JSON。缺素材時當設定檔損壞。"""
    game_code = config.get("game")
    items = config.get("items")
    if game_code not in SUPPORTED_GAMES or not isinstance(items, dict):
        raise HTTPException(status_code=500, detail="設定檔格式不對")
    npc = {
        "Start_NPC_Name": config.get("Start_NPC_Name") or "",
        "Start_Dialogues": config.get("Start_Dialogues") or [],
    }
    with db_conn() as connection:
        with connection.cursor() as cursor:
            if game_code in MARKET_GAMES:
                return assemble_market_play(
                    cursor, student_name, game_code, config, items, npc
                )
            if game_code == "SortArena":
                tag_codes = config.get("tags")
                if not isinstance(tag_codes, list) or len(tag_codes) != 4:
                    raise HTTPException(status_code=500, detail="設定檔格式不對")
                themes: list[dict[str, str]] = []
                for tag_code in tag_codes:
                    if not isinstance(tag_code, str) or not tag_code:
                        raise HTTPException(status_code=500, detail="設定檔格式不對")
                    tag = get_tag(cursor, tag_code)
                    themes.append({"code": tag["tag_code"], "name": tag["tag_name"]})
                return {
                    "game": game_code,
                    "studentName": student_name,
                    "themes": themes,
                    "slots": unity_slots(cursor, items, SORT_KEYS),
                    **npc,
                }
            tag_code = config.get("tag")
            if not isinstance(tag_code, str) or not tag_code:
                raise HTTPException(status_code=500, detail="設定檔格式不對")
            tag = get_tag(cursor, tag_code)
            theme = {"code": tag["tag_code"], "name": tag["tag_name"]}
            if game_code == "DecisionParkour":
                rows = []
                for index in range(1, 7):
                    rows.append(
                        {
                            "question": unity_item(cursor, items.get(f"theme_{index}")),
                            "distractor_1": unity_item(
                                cursor, items.get(f"distractor_{2 * index - 1}")
                            ),
                            "distractor_2": unity_item(
                                cursor, items.get(f"distractor_{2 * index}")
                            ),
                        }
                    )
                return {
                    "game": game_code,
                    "studentName": student_name,
                    "theme": theme,
                    "rows": rows,
                    **npc,
                }
            slot_keys = SLOT_KEYS if game_code == "MemoryMatch" else VACUUM_KEYS
            return {
                "game": game_code,
                "studentName": student_name,
                "theme": theme,
                "slots": unity_slots(cursor, items, slot_keys),
                **npc,
            }


@router.get("/games/{game_code}/materials/default")
def get_default_material(
    game_code: str, _teacher_id: int = Depends(current_teacher_id)
) -> dict:
    """回傳全站預設素材配置。未登入時 Depends 回傳 401。"""
    return load_default_payload(game_code)


@router.get("/students/{student_id}/games/{game_code}/materials")
def get_student_material(
    student_id: int, game_code: str, teacher_id: int = Depends(current_teacher_id)
) -> list[dict]:
    """回傳此學生此遊戲的自訂配置。沒有列時是空陣列。"""
    require_supported_game(game_code)
    with db_conn() as connection:
        with connection.cursor() as cursor:
            get_owned_student(cursor, teacher_id, student_id)
            game = get_game(cursor, game_code)
            cursor.execute(
                """
                SELECT id, json_path
                FROM GameMaterialCustomization
                WHERE teacher_id = %s AND student_id = %s AND game_id = %s
                ORDER BY id
                """,
                (teacher_id, student_id, game["id"]),
            )
            rows = cursor.fetchall()
    return [read_custom_material(row["id"], row["json_path"]) for row in rows]


@router.post("/students/{student_id}/games/{game_code}/materials", status_code=201)
def post_student_material(
    student_id: int,
    game_code: str,
    body: GameMaterialIn,
    teacher_id: int = Depends(current_teacher_id),
) -> dict:
    """先插入列並取得 id。再寫入遊戲代號子目錄的 json。失敗時回復該列。失敗時刪除未完成的檔。"""
    written: Path | None = None
    try:
        with db_conn(commit=True) as connection:
            with connection.cursor() as cursor:
                payload = clean_game_material(cursor, game_code, body)
                student = get_owned_student(cursor, teacher_id, student_id)
                teacher = get_teacher(cursor, teacher_id)
                game = get_game(cursor, game_code)
                cursor.execute(
                    """
                    INSERT INTO GameMaterialCustomization
                        (teacher_id, student_id, game_id, json_path)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (teacher_id, student_id, game["id"], ""),
                )
                config_id = int(cursor.lastrowid)
                relative = customization_json_path(
                    teacher["username"], student["username"], game_code, config_id
                )
                path = storage_file(relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                written = path
                path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                cursor.execute(
                    """
                    UPDATE GameMaterialCustomization
                    SET json_path = %s
                    WHERE id = %s
                    """,
                    (relative, config_id),
                )
    except Exception:
        if written is not None and written.is_file():
            written.unlink()
        raise
    return attach_material_identity(payload, config_id, relative)


@router.put("/students/{student_id}/games/{game_code}/materials/{config_id}")
def put_student_material(
    student_id: int,
    game_code: str,
    config_id: int,
    body: GameMaterialIn,
    teacher_id: int = Depends(current_teacher_id),
) -> dict:
    """寫回此列現有的 json_path。列必須屬於這位老師的這位學生。"""
    with db_conn(commit=True) as connection:
        with connection.cursor() as cursor:
            payload = clean_game_material(cursor, game_code, body)
            get_owned_student(cursor, teacher_id, student_id)
            game = get_game(cursor, game_code)
            cursor.execute(
                """
                SELECT game_id, json_path
                FROM GameMaterialCustomization
                WHERE id = %s AND teacher_id = %s AND student_id = %s
                """,
                (config_id, teacher_id, student_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="找不到這份素材配置")
            if row["game_id"] != game["id"]:
                raise HTTPException(status_code=400, detail="遊戲代碼不一致")
            relative = row["json_path"]
            path = storage_file(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            cursor.execute(
                """
                UPDATE GameMaterialCustomization
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (config_id,),
            )
    return attach_material_identity(payload, config_id, relative)
