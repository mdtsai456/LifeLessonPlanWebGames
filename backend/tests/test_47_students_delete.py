"""測試 47：刪除自己的學生後，列表沒有該學生。"""


def test_students_delete_ok(client, auth_headers):
    created = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_gone"},
    )
    assert created.status_code == 201, created.text
    student_id = created.json()["id"]

    deleted = client.delete(f"/api/students/{student_id}", headers=auth_headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["status"] == "deleted"

    listed = client.get("/api/students", headers=auth_headers)
    names = [row["username"] for row in listed.json()]
    assert "zz_pytest_student_gone" not in names


def test_students_delete_missing_is_404(client, auth_headers):
    response = client.delete("/api/students/999999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "找不到這位學生"
