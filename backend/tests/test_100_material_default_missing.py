"""測試 100：json_path 指向不存在的檔時回 404。測完還原。"""

from tests.conftest import first_memory_default_row, set_memory_default_path

MISSING_PATH = "GameMaterialDefault/zz_pytest_missing.json"


def test_memory_default_missing_file_is_404(client, auth_headers):
    row = first_memory_default_row()
    assert row is not None
    original = row["json_path"]
    set_memory_default_path(row["id"], MISSING_PATH)
    try:
        response = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers)
        assert response.status_code == 404, response.text
    finally:
        set_memory_default_path(row["id"], original)
