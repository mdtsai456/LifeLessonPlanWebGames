"""測試 99：格子網址去掉問號後，API 回傳內容等於資料庫 json_path 指向的檔。"""

import json

from backend.database import STORAGE_DIR
from tests.conftest import first_memory_default_row


def test_memory_default_matches_db_file(client, auth_headers):
    row = first_memory_default_row()
    assert row is not None
    expected = json.loads((STORAGE_DIR / row["json_path"]).read_text(encoding="utf-8"))
    response = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    actual = response.json()
    actual["items"] = {
        key: value.split("?", 1)[0] for key, value in actual["items"].items()
    }
    assert actual == expected
