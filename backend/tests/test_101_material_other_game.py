"""測試 101：未知遊戲不提供素材配置。"""


def test_unknown_game_default_is_400(client, auth_headers):
    response = client.get("/api/games/UnknownGame/materials/default", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "此遊戲配置尚未提供"
