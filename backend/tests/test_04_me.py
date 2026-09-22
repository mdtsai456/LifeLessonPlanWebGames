"""測試 4：未登入不可讀 /api/me。token 有效時回傳目前老師。"""


def test_me_without_token_is_401(client):
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "請重新登入"


def test_me_with_garbage_token_is_401(client):
    response = client.get("/api/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_with_token(client, auth_headers, test_teacher):
    response = client.get("/api/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == test_teacher["id"]
    assert body["username"] == test_teacher["username"]
