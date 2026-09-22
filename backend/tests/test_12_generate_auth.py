"""測試 12：生成 API 要登入。Unity 健康檢查不使用老師 token。"""


def test_generate_2d_needs_login(client):
    response = client.post("/api/tags/CARBS/generate-2d", json={"objectName": "箱子"})
    assert response.status_code == 401


def test_generate_3d_needs_login(client):
    response = client.post("/api/tags/CARBS/generate-3d", json={"prompt": "a red chair"})
    assert response.status_code == 401
