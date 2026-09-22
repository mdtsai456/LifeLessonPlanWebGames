"""測試 42：這位測試老師尚未新增學生時，列表為空。"""


def test_students_list_empty(client, auth_headers):
    response = client.get("/api/students", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json() == []
