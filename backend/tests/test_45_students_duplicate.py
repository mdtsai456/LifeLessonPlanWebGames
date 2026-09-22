"""測試 45：學生帳號全域唯一。帳號重複時回 409。"""


def test_students_duplicate_is_409(client, auth_headers):
    payload = {"username": "zz_pytest_student_dup"}
    first = client.post("/api/students", headers=auth_headers, json=payload)
    assert first.status_code == 201, first.text
    second = client.post("/api/students", headers=auth_headers, json=payload)
    assert second.status_code == 409
    assert "zz_pytest_student_dup" in second.json()["detail"]
