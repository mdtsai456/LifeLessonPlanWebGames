"""測試 5：登出會作廢 token。兩次登入互不影響。"""


def test_logout_revokes_token(client, test_teacher):
    login = client.post(
        "/api/auth/login",
        json={"username": test_teacher["username"], "password": test_teacher["password"]},
    )
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert logout.json()["status"] == "ok"

    me = client.get("/api/me", headers=headers)
    assert me.status_code == 401


def test_logout_without_token_is_ok(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_logout_one_session_keeps_the_other(client, test_teacher):
    body = {"username": test_teacher["username"], "password": test_teacher["password"]}
    first = client.post("/api/auth/login", json=body).json()["token"]
    second = client.post("/api/auth/login", json=body).json()["token"]

    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {first}"})

    still_ok = client.get("/api/me", headers={"Authorization": f"Bearer {second}"})
    assert still_ok.status_code == 200
    assert still_ok.json()["id"] == test_teacher["id"]
