"""測試 98：預設記憶配對是 4 正確 + 5 錯誤。預設記憶配對含開場 NPC 欄位。"""

from tests.conftest import DISTRACTOR_SLOT_KEYS, THEME_SLOT_KEYS


def test_memory_default_shape(client, auth_headers):
    body = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers).json()
    assert body["game"] == "MemoryMatch"
    assert isinstance(body["tag"], str) and body["tag"]
    assert set(body["items"]) == set(THEME_SLOT_KEYS + DISTRACTOR_SLOT_KEYS)
    assert all(isinstance(body["items"][key], str) and body["items"][key] for key in body["items"])
    assert all(body["items"][key].startswith("/static/") for key in body["items"])
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
