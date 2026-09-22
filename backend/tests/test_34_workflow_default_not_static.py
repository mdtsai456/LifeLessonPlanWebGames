"""測試 34：預設關卡 JSON 不能從 /static 直接下載。"""


def test_workflow_default_not_on_static(client):
    response = client.get("/static/GameWorkflowDefault/workflow.json")
    assert response.status_code != 200
