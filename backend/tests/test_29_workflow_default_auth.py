"""測試 29：預設關卡 API 要登入。"""


def test_workflow_default_needs_login(client):
    response = client.get("/api/workflow/default")
    assert response.status_code == 401
