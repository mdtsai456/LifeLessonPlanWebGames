"""測試 11：007 之後新增的分類與素材，不同遊戲不可共用。"""

from tests.conftest import TEST_TAG_NAME, make_tag


def test_other_game_same_tag_name_is_a_new_tag(client, auth_headers):
    first = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/games/MemoryMatch/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert second.status_code == 201, second.text
    assert second.json()["created_tag"] is True
    assert second.json()["code"] != first.json()["code"]
    assert second.json()["name"] == first.json()["name"] == TEST_TAG_NAME

    market = client.get("/api/games/MarketShopping/tags", headers=auth_headers).json()
    memory = client.get("/api/games/MemoryMatch/tags", headers=auth_headers).json()
    assert any(row["code"] == first.json()["code"] for row in market)
    assert all(row["code"] != first.json()["code"] for row in memory)
    assert any(row["code"] == second.json()["code"] for row in memory)
    assert all(row["code"] != second.json()["code"] for row in market)


def test_new_material_stays_on_that_game_only(client, auth_headers):
    market_tag = make_tag(client, auth_headers, game_code="MarketShopping")
    memory_tag = make_tag(client, auth_headers, game_code="MemoryMatch")

    created = client.post(
        f"/api/tags/{market_tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_只在超市"},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]

    market_list = client.get(f"/api/tags/{market_tag}/materials", headers=auth_headers).json()
    memory_list = client.get(f"/api/tags/{memory_tag}/materials", headers=auth_headers).json()
    assert any(item["code"] == code for item in market_list["materials"])
    assert all(item["code"] != code for item in memory_list["materials"])


def test_all_listed_games_can_add_isolated_tags(client, auth_headers):
    games = [row["code"] for row in client.get("/api/games", headers=auth_headers).json()]
    assert games
    codes = []
    for game_code in games:
        created = client.post(
            f"/api/games/{game_code}/tags",
            headers=auth_headers,
            json={"name": TEST_TAG_NAME},
        )
        assert created.status_code == 201, f"{game_code}: {created.text}"
        codes.append(created.json()["code"])

    assert len(set(codes)) == len(games)

    for game_code, own_code in zip(games, codes, strict=True):
        tags = client.get(f"/api/games/{game_code}/tags", headers=auth_headers).json()
        found = {row["code"] for row in tags if row["name"] == TEST_TAG_NAME}
        assert found == {own_code}, game_code
