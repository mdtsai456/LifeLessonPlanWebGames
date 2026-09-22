"""測試 141：超市購物空貨架、非法格子、缺價格、空清單會 400。"""

from tests.conftest import make_market_shopping_config, make_student


def test_market_empty_shelf_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_empty")
    payload = make_market_shopping_config(client, auth_headers)
    payload["items"] = {}
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "至少要放一件商品"


def test_market_illegal_slot_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_slot")
    payload = make_market_shopping_config(client, auth_headers)
    payload["items"]["shelf_nope_1"] = payload["items"]["shelf_regular_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "貨架格子不合法"


def test_market_missing_price_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_price")
    payload = make_market_shopping_config(client, auth_headers)
    payload["prices"] = {}
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "每個已上架商品都要有價格"


def test_market_empty_basket_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_basket")
    payload = make_market_shopping_config(client, auth_headers)
    payload["basketOrder"] = []
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "購物清單不能是空的"
