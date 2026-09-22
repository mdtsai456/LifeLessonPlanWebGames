"""測試 145：預算模式空貨架、非法格子、缺價格、預算須大於 0。"""

from tests.conftest import make_market_budget_config, make_student


def test_market_budget_empty_shelf_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_empty")
    payload = make_market_budget_config(client, auth_headers)
    payload["items"] = {}
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "至少要放一件商品"


def test_market_budget_illegal_slot_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_slot")
    payload = make_market_budget_config(client, auth_headers)
    payload["items"]["shelf_nope_1"] = payload["items"]["shelf_regular_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "貨架格子不合法"


def test_market_budget_missing_price_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_price")
    payload = make_market_budget_config(client, auth_headers)
    payload["prices"] = {}
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "每個已上架商品都要有價格"


def test_market_budget_not_positive_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_zero")
    payload = make_market_budget_config(client, auth_headers)
    payload["budget"] = 0
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "預算必須大於 0"
