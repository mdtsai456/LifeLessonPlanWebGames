"""測試 30：登入後可讀取預設關卡。"""


def test_workflow_default_ok(client, auth_headers):
    response = client.get("/api/workflow/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "storylines" in body
    assert isinstance(body["storylines"], list)
    assert len(body["storylines"]) > 0
