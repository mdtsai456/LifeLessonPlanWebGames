"""測試共用。建立暫存老師。刪除 zz_pytest_ 分類與素材。"""

import os
from contextlib import contextmanager
from pathlib import Path

import bcrypt
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)
# 測試不使用 GPU。Unity key 固定。不讀取本機 .env 的值。
os.environ["TEXT2IMAGE_MOCK"] = "1"
os.environ["TRELLIS_MOCK"] = "1"
UNITY_TEST_KEY = "zz_pytest_unity_key"
os.environ["UNITY_API_KEY"] = UNITY_TEST_KEY

from backend.database import STATIC_DIR, STORAGE_DIR, connect_db
from backend.main import app

TEST_USERNAME = "zz_pytest_auth"
TEST_USERNAME_B = "zz_pytest_auth_b"
TEST_PASSWORD = "Test1234"
TEST_TAG_NAME = "zz_pytest_分類"
TEST_STUDENT_PREFIX = "zz_pytest_student_"

# /api/games 必須含這些 code。額外的遊戲不造成測試失敗。
REQUIRED_GAMES = {
    "MarketShopping",
    "MarketShoppingBudgetMode",
    "MemoryMatch",
    "PairVacuum",
    "SortArena",
    "DecisionParkour",
}

# 超市購物目前的種子分類。額外的分類不造成測試失敗。
REQUIRED_MARKET_TAGS = {
    "CARBS",
    "DRINK",
    "FRUIT",
    "MEAT",
    "VEGETABLE",
}

# 測自訂關卡時把 Default 順序反轉。確認 GET 不是在讀種子檔。
SIX_GAMES_REVERSED = [
    {"game": "MarketShoppingBudgetMode", "order": 1},
    {"game": "DecisionParkour", "order": 2},
    {"game": "SortArena", "order": 3},
    {"game": "PairVacuum", "order": 4},
    {"game": "MemoryMatch", "order": 5},
    {"game": "MarketShopping", "order": 6},
]


def workflow_body(
    games: list[dict[str, object]],
    *,
    name: str = "預設",
    start_npc: str = "",
    start_dialogues: list[str] | None = None,
) -> dict[str, object]:
    """把步驟包成一條故事線。保留呼叫端給的閉場。不補預設。"""
    steps: list[dict[str, object]] = []
    for item in games:
        step: dict[str, object] = {"game": item["game"], "order": item["order"]}
        if "gameMaterialCustomizationId" in item:
            step["gameMaterialCustomizationId"] = item["gameMaterialCustomizationId"]
        if "endNpcName" in item:
            step["endNpcName"] = item["endNpcName"]
        if "endDialogues" in item:
            step["endDialogues"] = item["endDialogues"]
        steps.append(step)
    return {
        "startNpcName": start_npc,
        "startDialogues": list(start_dialogues or []),
        "storylines": [{"name": name, "order": 1, "steps": steps}],
    }


def saved_workflow_games(
    games: list[dict[str, object]],
    *,
    name: str = "預設",
    start_npc: str = "",
    start_dialogues: list[str] | None = None,
) -> dict[str, object]:
    """PUT 後的故事線。每步補上素材 id。沒給閉場時為空字串。沒給閉場時為空陣列。"""
    steps: list[dict[str, object]] = []
    for item in games:
        steps.append(
            {
                "game": item["game"],
                "gameMaterialCustomizationId": item.get("gameMaterialCustomizationId"),
                "order": item["order"],
                "endNpcName": item.get("endNpcName", ""),
                "endDialogues": list(item.get("endDialogues", [])),
            }
        )
    return {
        "startNpcName": start_npc,
        "startDialogues": list(start_dialogues or []),
        "storylines": [{"name": name, "order": 1, "steps": steps}],
    }


def storyline_steps(body: dict[str, object]) -> list[dict[str, object]]:
    """取出第一條故事線的步驟。"""
    lines = body["storylines"]
    return lines[0]["steps"]

# 1x1 透明 PNG。用來測上傳。不必開啟圖檔。
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0ab4000000000049454e44ae426082"
)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


def _upsert_teacher(username: str) -> dict[str, object]:
    password_hash = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM Teacher WHERE username = %s", (username,))
            existing = cursor.fetchone()
            if existing:
                _delete_students_for_teacher(cursor, existing["id"])
            cursor.execute("DELETE FROM Teacher WHERE username = %s", (username,))
            cursor.execute(
                "INSERT INTO Teacher (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
            teacher_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()
    return {"id": teacher_id, "username": username, "password": TEST_PASSWORD}


def _delete_students_for_teacher(cursor, teacher_id: int) -> None:
    """Student 對 Teacher 沒有 ON DELETE CASCADE。刪除老師前必須先刪學生。"""
    cursor.execute(
        "DELETE FROM GameMaterialCustomization WHERE teacher_id = %s",
        (teacher_id,),
    )
    cursor.execute(
        "DELETE FROM GameWorkflowCustomization WHERE teacher_id = %s",
        (teacher_id,),
    )
    cursor.execute("DELETE FROM Student WHERE teacher_id = %s", (teacher_id,))


def _delete_teacher(username: str) -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM Teacher WHERE username = %s", (username,))
            row = cursor.fetchone()
            if row:
                _delete_students_for_teacher(cursor, row["id"])
            cursor.execute("DELETE FROM Teacher WHERE username = %s", (username,))
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="session")
def test_teacher() -> dict[str, object]:
    """測試用老師。不修改資料庫裡原本的帳號。"""
    teacher = _upsert_teacher(TEST_USERNAME)
    yield teacher
    _delete_teacher(TEST_USERNAME)


@pytest.fixture(scope="session")
def other_teacher() -> dict[str, object]:
    """第二位老師。用來確認素材庫跨老師看得到同一份資料。"""
    teacher = _upsert_teacher(TEST_USERNAME_B)
    yield teacher
    _delete_teacher(TEST_USERNAME_B)


@pytest.fixture
def auth_headers(client: TestClient, test_teacher: dict[str, object]) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": test_teacher["username"], "password": test_teacher["password"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(client: TestClient, other_teacher: dict[str, object]) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": other_teacher["username"], "password": other_teacher["password"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def cleanup_pytest_library_rows():
    """每則測試前後刪除 zz_pytest_ 開頭的分類、素材、學生。種子資料不修改。"""
    _delete_pytest_library_rows()
    _delete_pytest_students()
    yield
    _delete_pytest_library_rows()
    _delete_pytest_students()
    _delete_tmp_files()
    _delete_pytest_workflow_custom_files()
    _delete_pytest_material_custom_files()


def make_tag(
    client: TestClient,
    headers: dict[str, str],
    game_code: str = "MarketShopping",
    name: str = TEST_TAG_NAME,
) -> str:
    created = client.post(
        f"/api/games/{game_code}/tags",
        headers=headers,
        json={"name": name},
    )
    assert created.status_code == 201, created.text
    return created.json()["code"]


def listed_game_codes(client: TestClient, headers: dict[str, str]) -> set[str]:
    """讀目前資料庫的遊戲 code。不要寫死數量。"""
    response = client.get("/api/games", headers=headers)
    assert response.status_code == 200, response.text
    return {row["code"] for row in response.json()}


def listed_tags(client: TestClient, headers: dict[str, str], game_code: str) -> list[dict]:
    """讀一款遊戲目前的分類。"""
    response = client.get(f"/api/games/{game_code}/tags", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list)
    return body


def make_student(
    client: TestClient,
    headers: dict[str, str],
    username: str = "zz_pytest_student_wf",
) -> dict[str, object]:
    created = client.post(
        "/api/students",
        headers=headers,
        json={"username": username},
    )
    assert created.status_code == 201, created.text
    return created.json()


def _delete_tmp_files() -> None:
    tmp_dir = STATIC_DIR / "GameMaterial" / "tmp"
    if not tmp_dir.is_dir():
        return
    for path in tmp_dir.iterdir():
        if path.is_file() and path.name != ".gitkeep":
            path.unlink()


def _delete_pytest_students() -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, teacher_id FROM Student WHERE username LIKE %s",
                (f"{TEST_STUDENT_PREFIX}%",),
            )
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute(
                    "DELETE FROM GameMaterialCustomization WHERE student_id = %s AND teacher_id = %s",
                    (row["id"], row["teacher_id"]),
                )
                cursor.execute(
                    "DELETE FROM GameWorkflowCustomization WHERE student_id = %s AND teacher_id = %s",
                    (row["id"], row["teacher_id"]),
                )
                cursor.execute(
                    "DELETE FROM Student WHERE id = %s AND teacher_id = %s",
                    (row["id"], row["teacher_id"]),
                )
        connection.commit()
    finally:
        connection.close()


def _delete_pytest_workflow_custom_files() -> None:
    root = STORAGE_DIR / "GameWorkflowCustomization"
    if not root.is_dir():
        return
    for teacher_dir in root.iterdir():
        if not teacher_dir.is_dir() or not teacher_dir.name.startswith("zz_pytest_"):
            continue
        for student_dir in teacher_dir.iterdir():
            if not student_dir.is_dir():
                continue
            workflow = student_dir / "workflow.json"
            workflow.unlink(missing_ok=True)
            if not any(student_dir.iterdir()):
                student_dir.rmdir()
        if not any(teacher_dir.iterdir()):
            teacher_dir.rmdir()


def _delete_pytest_material_custom_files() -> None:
    root = STORAGE_DIR / "GameMaterialCustomization"
    if not root.is_dir():
        return
    for teacher_dir in root.iterdir():
        if not teacher_dir.is_dir() or not teacher_dir.name.startswith("zz_pytest_"):
            continue
        for student_dir in teacher_dir.iterdir():
            if not student_dir.is_dir():
                continue
            for path in student_dir.rglob("*.json"):
                if path.is_file():
                    path.unlink(missing_ok=True)
            for path in sorted(student_dir.rglob("*"), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
            if student_dir.is_dir() and not any(student_dir.iterdir()):
                student_dir.rmdir()
        if not any(teacher_dir.iterdir()):
            teacher_dir.rmdir()


def _delete_pytest_library_rows() -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM Tag WHERE tag_name LIKE %s", ("zz_pytest_%",))
            tag_ids = [row["id"] for row in cursor.fetchall()]
            if not tag_ids:
                connection.commit()
                return
            placeholders = ", ".join(["%s"] * len(tag_ids))
            cursor.execute(
                f"""
                SELECT gm.id, gm.file_path
                FROM GameMaterial gm
                JOIN GameMaterialTag gmt ON gmt.game_material_id = gm.id
                WHERE gmt.tag_id IN ({placeholders})
                  AND gm.material_name LIKE %s
                """,
                [*tag_ids, "zz_pytest_%"],
            )
            materials = cursor.fetchall()
            material_ids = [row["id"] for row in materials]
            if material_ids:
                mat_ph = ", ".join(["%s"] * len(material_ids))
                cursor.execute(
                    f"DELETE FROM GameMaterialTag WHERE game_material_id IN ({mat_ph})",
                    material_ids,
                )
                cursor.execute(f"DELETE FROM GameMaterial WHERE id IN ({mat_ph})", material_ids)
            cursor.execute(f"DELETE FROM GameTag WHERE tag_id IN ({placeholders})", tag_ids)
            cursor.execute(f"DELETE FROM Tag WHERE id IN ({placeholders})", tag_ids)
            connection.commit()
            for row in materials:
                path = (STATIC_DIR / row["file_path"]).resolve()
                if path.is_relative_to(STATIC_DIR.resolve()) and path.exists():
                    path.unlink()
    finally:
        connection.close()


def first_workflow_default_row() -> dict | None:
    """預設關卡那一列。測缺檔或壞檔時改 json_path。測完還原。"""
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, json_path FROM GameWorkflowDefault ORDER BY id LIMIT 1")
            return cursor.fetchone()
    finally:
        connection.close()


def set_workflow_default_path(row_id: int, json_path: str) -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE GameWorkflowDefault SET json_path = %s WHERE id = %s",
                (json_path, row_id),
            )
        connection.commit()
    finally:
        connection.close()


def first_memory_default_row() -> dict | None:
    """記憶配對 Default 那一列。測缺檔時改 json_path。測完還原。"""
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT gmd.id, gmd.json_path
                FROM GameMaterialDefault gmd
                JOIN Game g ON g.id = gmd.game_id
                WHERE g.game_code = %s
                LIMIT 1
                """,
                ("MemoryMatch",),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def set_memory_default_path(row_id: int, json_path: str) -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE GameMaterialDefault SET json_path = %s WHERE id = %s",
                (json_path, row_id),
            )
        connection.commit()
    finally:
        connection.close()


THEME_SLOT_KEYS = ("theme_1", "theme_2", "theme_3", "theme_4")
DISTRACTOR_SLOT_KEYS = (
    "distractor_1",
    "distractor_2",
    "distractor_3",
    "distractor_4",
    "distractor_5",
)
VACUUM_SLOT_KEYS = ("slot_1", "slot_2", "slot_3", "slot_4", "slot_5")
PARKOUR_THEME_KEYS = tuple(f"theme_{index}" for index in range(1, 7))
PARKOUR_DISTRACTOR_KEYS = tuple(f"distractor_{index}" for index in range(1, 13))
SORT_SLOT_KEYS = tuple(
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


def make_memory_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立兩個測試分類與 4+5 個素材。回傳可通過驗證的 MemoryMatch body。"""
    theme_tag = make_tag(client, headers, game_code="MemoryMatch", name="zz_pytest_正確主題")
    other_tag = make_tag(client, headers, game_code="MemoryMatch", name="zz_pytest_干擾主題")
    theme_codes: list[str] = []
    distractor_codes: list[str] = []
    for index in range(4):
        created = client.post(
            f"/api/tags/{theme_tag}/materials",
            headers=headers,
            data={"name": f"zz_pytest_對{index}"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        theme_codes.append(body.get("image_url") or body.get("model_url") or body["code"])
    for index in range(5):
        created = client.post(
            f"/api/tags/{other_tag}/materials",
            headers=headers,
            data={"name": f"zz_pytest_錯{index}"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        distractor_codes.append(body.get("image_url") or body.get("model_url") or body["code"])
    items = {key: theme_codes[index] for index, key in enumerate(THEME_SLOT_KEYS)}
    items.update(
        {key: distractor_codes[index] for index, key in enumerate(DISTRACTOR_SLOT_KEYS)}
    )
    return {
        "game": "MemoryMatch",
        "tag": theme_tag,
        "items": items,
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請找出可以吃的食物"]),
    }


def _pytest_material_urls(
    client: TestClient,
    headers: dict[str, str],
    tag_code: str,
    name_prefix: str,
    count: int,
) -> list[str]:
    urls: list[str] = []
    for index in range(count):
        created = client.post(
            f"/api/tags/{tag_code}/materials",
            headers=headers,
            data={"name": f"{name_prefix}{index}"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        urls.append(body.get("image_url") or body.get("model_url") or body["code"])
    return urls


def make_vacuum_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立一個測試分類與 5 個素材。回傳可通過驗證的 PairVacuum body。"""
    theme_tag = make_tag(client, headers, game_code="PairVacuum", name="zz_pytest_吸塵主題")
    theme_codes = _pytest_material_urls(
        client, headers, theme_tag, "zz_pytest_吸", 5
    )
    items = {key: theme_codes[index] for index, key in enumerate(VACUUM_SLOT_KEYS)}
    return {
        "game": "PairVacuum",
        "tag": theme_tag,
        "items": items,
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請吸起同一類物品"]),
    }


def make_parkour_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立兩個測試分類與 6+12 個素材。回傳可通過驗證的 DecisionParkour body。"""
    theme_tag = make_tag(client, headers, game_code="DecisionParkour", name="zz_pytest_跑酷正確")
    other_tag = make_tag(client, headers, game_code="DecisionParkour", name="zz_pytest_跑酷干擾")
    theme_codes = _pytest_material_urls(
        client, headers, theme_tag, "zz_pytest_跑對", 6
    )
    distractor_codes = _pytest_material_urls(
        client, headers, other_tag, "zz_pytest_跑錯", 12
    )
    items = {key: theme_codes[index] for index, key in enumerate(PARKOUR_THEME_KEYS)}
    items.update(
        {key: distractor_codes[index] for index, key in enumerate(PARKOUR_DISTRACTOR_KEYS)}
    )
    return {
        "game": "DecisionParkour",
        "tag": theme_tag,
        "items": items,
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請選對的路"]),
    }


def make_sort_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立四個測試分類各 5 個素材。回傳可通過驗證的 SortArena body。"""
    tags: list[str] = []
    items: dict[str, str] = {}
    for bin_index in range(1, 5):
        tag = make_tag(
            client,
            headers,
            game_code="SortArena",
            name=f"zz_pytest_分類主題{bin_index}",
        )
        tags.append(tag)
        urls = _pytest_material_urls(
            client, headers, tag, f"zz_pytest_桶{bin_index}_", 5
        )
        for slot_index, url in enumerate(urls, start=1):
            items[f"bin_{bin_index}_{slot_index}"] = url
    return {
        "game": "SortArena",
        "tags": tags,
        "items": items,
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請推進對的箱子"]),
    }


def _pytest_market_materials(
    client: TestClient,
    headers: dict[str, str],
    name_prefix: str,
    count: int,
) -> list[dict[str, object]]:
    """素材掛在 MarketShopping。預算模式驗證也不要求該遊戲 Tag。"""
    tag = make_tag(
        client, headers, game_code="MarketShopping", name=f"zz_pytest_{name_prefix}主題"
    )
    rows: list[dict[str, object]] = []
    for index in range(count):
        created = client.post(
            f"/api/tags/{tag}/materials",
            headers=headers,
            data={"name": f"zz_pytest_{name_prefix}{index}"},
        )
        assert created.status_code == 201, created.text
        rows.append(created.json())
    return rows


def make_market_shopping_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立兩個測試商品。回傳可通過驗證的 MarketShopping body。"""
    rows = _pytest_market_materials(client, headers, "超商", 2)
    first, second = rows
    items = {
        "shelf_regular_1": first.get("image_url") or first["code"],
        "shelf_fruit_1": second.get("image_url") or second["code"],
    }
    return {
        "game": "MarketShopping",
        "items": items,
        "basketOrder": [first["code"], second["code"]],
        "prices": {first["code"]: 15, second["code"]: 20},
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請依購物清單拿商品"]),
    }


def make_market_budget_config(
    client: TestClient,
    headers: dict[str, str],
    npc_name: str = "阿姨",
    dialogues: list[str] | None = None,
) -> dict[str, object]:
    """建立兩個測試商品。回傳可通過驗證的 MarketShoppingBudgetMode body。"""
    rows = _pytest_market_materials(client, headers, "預算", 2)
    first, second = rows
    items = {
        "shelf_regular_1": first.get("image_url") or first["code"],
        "shelf_fruit_1": second.get("image_url") or second["code"],
    }
    return {
        "game": "MarketShoppingBudgetMode",
        "items": items,
        "budget": 100,
        "prices": {first["code"]: 15, second["code"]: 20},
        "Start_NPC_Name": npc_name,
        "Start_Dialogues": list(dialogues or ["請在預算內選購商品"]),
    }


@contextmanager
def write_pytest_workflow_file(name: str, text: str):
    """寫入測試用 JSON。結束後刪檔。回傳相對 json_path。"""
    folder = STORAGE_DIR / "GameWorkflowDefault"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    try:
        yield f"GameWorkflowDefault/{name}"
    finally:
        path.unlink(missing_ok=True)


FRONTEND_JS_DIR = BACKEND_DIR.parent / "frontend" / "js"


def frontend_js_source() -> str:
    """讀取 frontend/js 全部 .js，給拆檔後的字串測試用。"""
    parts = [path.read_text(encoding="utf-8") for path in sorted(FRONTEND_JS_DIR.glob("*.js"))]
    return "\n".join(parts)


def js_function(source: str, name: str) -> str:
    """從傳入的非空字串取出 function 本體。空字串仍讀 frontend/js。範圍到下一支 function 之前。"""
    text = source if source else frontend_js_source()
    start = text.find(f"async function {name}(")
    if start < 0:
        start = text.find(f"function {name}(")
    if start < 0:
        raise AssertionError(f"找不到 function {name}")
    next_plain = text.find("\nfunction ", start + 1)
    next_async = text.find("\nasync function ", start + 1)
    ends = [index for index in (next_plain, next_async) if index >= 0]
    end = min(ends) if ends else len(text)
    return text[start:end]
