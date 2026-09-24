"""測試 139：超市購物 Default 可讀。超市購物 Default 含稀疏貨架。超市購物 Default 含價格。超市購物 Default 含購物清單。"""

from tests.conftest import MARKET_SLOT_KEYS

MARKET_DEFAULT_CODES = {
    "shelf_regular_1": "MAT145",
    "shelf_veg_1": "MAT137",
    "shelf_veg_2": "MAT138",
    "shelf_veg_3": "MAT141",
    "shelf_fruit_1": "MAT003",
    "shelf_fruit_2": "MAT004",
    "shelf_fruit_5": "MAT147",
}
MARKET_DEFAULT_PRICES = {
    "MAT145": 25,
    "MAT137": 30,
    "MAT138": 35,
    "MAT141": 15,
    "MAT003": 20,
    "MAT004": 15,
    "MAT147": 28,
}
MARKET_DEFAULT_BASKET = ["MAT003", "MAT137"]


def test_market_default_ok(client, auth_headers):
    response = client.get("/api/games/MarketShopping/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MarketShopping"
    assert "items" in body
    assert "prices" in body
    assert "basketOrder" in body


def test_market_default_shape(client, auth_headers):
    body = client.get("/api/games/MarketShopping/materials/default", headers=auth_headers).json()
    assert len(MARKET_SLOT_KEYS) == 40
    assert set(body["items"]) == set(MARKET_DEFAULT_CODES)
    assert set(body["items"]).issubset(MARKET_SLOT_KEYS)
    for key, code in MARKET_DEFAULT_CODES.items():
        assert body["items"][key].startswith("/static/")
        assert code in body["items"][key]
    assert body["prices"] == MARKET_DEFAULT_PRICES
    assert body["basketOrder"] == MARKET_DEFAULT_BASKET
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
