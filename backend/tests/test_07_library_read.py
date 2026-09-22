"""測試 7：只讀種子資料。分類與素材形狀依目前資料庫，不寫死 PARK。"""

from tests.conftest import REQUIRED_MARKET_TAGS, listed_tags


def test_market_shopping_has_required_tags(client, auth_headers):
    tags = listed_tags(client, auth_headers, "MarketShopping")
    assert tags, "超市購物應該已有分類"
    codes = {row["code"] for row in tags}
    missing = REQUIRED_MARKET_TAGS - codes
    assert not missing, f"超市購物缺少分類：{sorted(missing)}"
    assert all("code" in row and "name" in row for row in tags)


def test_other_games_have_their_own_tags(client, auth_headers):
    for game_code in ("MemoryMatch", "PairVacuum", "SortArena", "DecisionParkour"):
        tags = listed_tags(client, auth_headers, game_code)
        assert tags, f"{game_code} 應該已有分類"


def test_market_tag_materials_shape(client, auth_headers):
    tags = listed_tags(client, auth_headers, "MarketShopping")
    first = tags[0]
    response = client.get(f"/api/tags/{first['code']}/materials", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == first["code"]
    assert body["name"]
    assert len(body["materials"]) >= 1
    item = body["materials"][0]
    assert item["code"].startswith("MAT")
    assert item["name"]
    assert item["image_url"].startswith("/static/GameMaterial/Shared/")
