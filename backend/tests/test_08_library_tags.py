"""測試 8：新增或刪除分類。同一遊戲不可重複名稱。其他遊戲同名須另開一筆。"""

from tests.conftest import TEST_TAG_NAME, make_tag


def test_blank_tag_name_is_400(client, auth_headers):
    response = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": "   "},
    )
    assert response.status_code == 400


def test_add_tag_then_see_it_on_that_game(client, auth_headers):
    created = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["created_tag"] is True
    assert body["name"] == TEST_TAG_NAME
    assert body["code"].startswith("TAG")

    tags = client.get("/api/games/MarketShopping/tags", headers=auth_headers).json()
    assert any(row["code"] == body["code"] and row["name"] == TEST_TAG_NAME for row in tags)


def test_same_game_cannot_add_same_tag_twice(client, auth_headers):
    first = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert second.status_code == 409


def test_delete_tag_only_unlinks_that_game(client, auth_headers):
    code = make_tag(client, auth_headers)
    removed = client.delete(
        f"/api/games/MarketShopping/tags/{code}",
        headers=auth_headers,
    )
    assert removed.status_code == 200
    assert removed.json()["status"] == "deleted"

    market = client.get("/api/games/MarketShopping/tags", headers=auth_headers).json()
    assert all(row["code"] != code for row in market)


def test_delete_unknown_tag_on_game_is_404(client, auth_headers):
    response = client.delete(
        "/api/games/MarketShopping/tags/NOT_A_TAG",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_delete_tag_that_is_not_on_this_game_is_404(client, auth_headers):
    code = make_tag(client, auth_headers, game_code="MemoryMatch")
    response = client.delete(
        f"/api/games/MarketShopping/tags/{code}",
        headers=auth_headers,
    )
    assert response.status_code == 404
    memory = client.get("/api/games/MemoryMatch/tags", headers=auth_headers).json()
    assert any(row["code"] == code for row in memory)
