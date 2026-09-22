"""測試 44：新增後列表看得到。依帳號排序。"""


def test_students_list_after_create(client, auth_headers):
    first = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_b"},
    )
    second = client.post(
        "/api/students",
        headers=auth_headers,
        json={"username": "zz_pytest_student_a"},
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    response = client.get("/api/students", headers=auth_headers)
    assert response.status_code == 200, response.text
    names = [row["username"] for row in response.json()]
    assert names == ["zz_pytest_student_a", "zz_pytest_student_b"]
