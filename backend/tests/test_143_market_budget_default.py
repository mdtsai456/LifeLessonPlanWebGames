"""測試 143：超市購物預算模式 Default 可讀，有預算、無購物清單。"""

from tests.conftest import MARKET_SLOT_KEYS

BUDGET_DEFAULT_CODES = {
    "shelf_regular_1": "MAT145",
    "shelf_veg_1": "MAT137",
    "shelf_veg_2": "MAT138",
    "shelf_veg_3": "MAT141",
    "shelf_fruit_1": "MAT003",
    "shelf_fruit_2": "MAT004",
    "shelf_fruit_5": "MAT147",
}
BUDGET_DEFAULT_PRICES = {
    "MAT145": 25,
    "MAT137": 30,
    "MAT138": 35,
    "MAT141": 15,
    "MAT003": 20,
    "MAT004": 15,
    "MAT147": 28,
}


def test_market_budget_default_ok(client, auth_headers):
    response = client.get(
        "/api/games/MarketShoppingBudgetMode/materials/default", headers=auth_headers
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MarketShoppingBudgetMode"
    assert "items" in body
    assert "prices" in body
    assert "budget" in body


def test_market_budget_default_shape(client, auth_headers):
    body = client.get(
        "/api/games/MarketShoppingBudgetMode/materials/default", headers=auth_headers
    ).json()
    assert set(body["items"]) == set(BUDGET_DEFAULT_CODES)
    assert set(body["items"]).issubset(MARKET_SLOT_KEYS)
    for key, code in BUDGET_DEFAULT_CODES.items():
        assert body["items"][key].startswith("/static/")
        assert code in body["items"][key]
    assert body["prices"] == BUDGET_DEFAULT_PRICES
    assert body["budget"] == 100
    assert not body.get("basketOrder")
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
