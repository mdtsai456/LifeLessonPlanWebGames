"""測試 40：預設關卡這一輪只有 GET。"""


def test_workflow_default_post_not_allowed(client, auth_headers):
    response = client.post("/api/workflow/default", headers=auth_headers, json={})
    assert response.status_code == 405
