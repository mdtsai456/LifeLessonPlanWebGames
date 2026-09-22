"""測試 96：預設記憶配對 API 要登入。"""


def test_memory_default_needs_login(client):
    response = client.get("/api/games/MemoryMatch/materials/default")
    assert response.status_code == 401
