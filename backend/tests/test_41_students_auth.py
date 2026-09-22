"""測試 41：學生 API 要登入。"""


def test_students_list_needs_login(client):
    response = client.get("/api/students")
    assert response.status_code == 401


def test_students_create_needs_login(client):
    response = client.post("/api/students", json={"username": "zz_pytest_student_nologin"})
    assert response.status_code == 401


def test_students_delete_needs_login(client):
    response = client.delete("/api/students/1")
    assert response.status_code == 401
