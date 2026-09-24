"""測試 46：其他老師看不到這位學生。其他老師刪不掉這位學生。"""


def test_other_teacher_does_not_see_student(
    client, auth_headers, other_auth_headers
):
    created = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_owner"},
    )
    assert created.status_code == 201, created.text

    listed = client.get("/api/students", headers=other_auth_headers)
    assert listed.status_code == 200, listed.text
    names = [row["username"] for row in listed.json()]
    assert "zz_pytest_student_owner" not in names


def test_other_teacher_cannot_delete_student(
    client, auth_headers, other_auth_headers
):
    created = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_keep"},
    )
    assert created.status_code == 201, created.text
    student_id = created.json()["id"]

    deleted = client.delete(
        f"/api/students/{student_id}",
        headers=other_auth_headers,
    )
    assert deleted.status_code == 404

    listed = client.get("/api/students", headers=auth_headers)
    names = [row["username"] for row in listed.json()]
    assert "zz_pytest_student_keep" in names
