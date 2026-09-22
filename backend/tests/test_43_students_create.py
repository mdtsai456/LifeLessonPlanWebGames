"""測試 43：新增學生回傳 id 與帳號。"""


def test_students_create_ok(client, auth_headers):
    response = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_create"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["username"] == "zz_pytest_student_create"
    assert body["id"]


def test_students_create_trims_username(client, auth_headers):
    response = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "  zz_pytest_student_trim  "},
    )
    assert response.status_code == 201, response.text
    assert response.json()["username"] == "zz_pytest_student_trim"


def test_students_create_blank_is_400(client, auth_headers):
    response = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "   "},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "請輸入學生帳號"
