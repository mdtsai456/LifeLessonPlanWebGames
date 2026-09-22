"""測試 6：素材庫 API 要登入。必要遊戲 code 都要在清單裡。"""

from tests.conftest import REQUIRED_GAMES, listed_game_codes

LIBRARY_GETS = [
    "/api/games",
    "/api/games/MarketShopping/tags",
    "/api/games/MarketShopping/library",
    "/api/tags/CARBS/materials",
]


def test_library_reads_need_login(client):
    for path in LIBRARY_GETS:
        response = client.get(path)
        assert response.status_code == 401, path


def test_library_writes_need_login(client):
    post_tag = client.post("/api/games/MarketShopping/tags", json={"name": "zz_pytest_未登入"})
    assert post_tag.status_code == 401

    post_material = client.post("/api/tags/CARBS/materials", data={"name": "zz_pytest_未登入"})
    assert post_material.status_code == 401

    patch_name = client.patch("/api/materials/MAT003", json={"name": "zz_pytest_未登入"})
    assert patch_name.status_code == 401

    delete_tag = client.delete("/api/games/MarketShopping/tags/CARBS")
    assert delete_tag.status_code == 401


def test_required_games_are_listed(client, auth_headers):
    codes = listed_game_codes(client, auth_headers)
    missing = REQUIRED_GAMES - codes
    assert not missing, f"缺少遊戲：{sorted(missing)}"
    body = client.get("/api/games", headers=auth_headers).json()
    assert "超市購物" in {row["name"] for row in body}
    assert all("code" in row and "name" in row for row in body)


def test_unknown_game_tags_are_404(client, auth_headers):
    response = client.get("/api/games/NotAGame/tags", headers=auth_headers)
    assert response.status_code == 404


def test_unknown_tag_materials_are_404(client, auth_headers):
    response = client.get("/api/tags/NOT_A_TAG/materials", headers=auth_headers)
    assert response.status_code == 404
