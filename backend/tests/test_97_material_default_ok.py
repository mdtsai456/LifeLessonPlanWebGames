"""測試 97：登入後可讀取預設記憶配對。"""


def test_memory_default_ok(client, auth_headers):
    response = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MemoryMatch"
    assert "tag" in body
    assert "items" in body
