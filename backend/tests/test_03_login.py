"""測試 3：登入成功才取得 token。帳密錯誤都回 401。"""


def test_wrong_password_is_401(client, test_teacher):
    response = client.post(
        "/api/auth/login",
        json={"username": test_teacher["username"], "password": "not-the-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "帳號或密碼不對"


def test_unknown_user_is_401(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "__no_such_teacher__", "password": "x"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "帳號或密碼不對"


def test_login_ok(client, test_teacher):
    response = client.post(
        "/api/auth/login",
        json={"username": test_teacher["username"], "password": test_teacher["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["teacher"]["id"] == test_teacher["id"]
    assert body["teacher"]["username"] == test_teacher["username"]


def test_login_trims_username(client, test_teacher):
    response = client.post(
        "/api/auth/login",
        json={
            "username": f"  {test_teacher['username']}  ",
            "password": test_teacher["password"],
        },
    )
    assert response.status_code == 200
    assert response.json()["teacher"]["username"] == test_teacher["username"]
