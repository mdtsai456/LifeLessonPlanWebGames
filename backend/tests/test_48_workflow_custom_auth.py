"""測試 48：學生關卡 API 要登入。"""


def test_student_workflow_get_needs_login(client):
    response = client.get("/api/students/1/workflow")
    assert response.status_code == 401


def test_student_workflow_put_needs_login(client):
    response = client.put(
        "/api/students/1/workflow",
        json={"startNpcName": "", "startDialogues": [], "storylines": []},
    )
    assert response.status_code == 401
