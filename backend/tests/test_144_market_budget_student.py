"""測試 144：預算模式沒自訂退回 Default；PUT 後 GET 讀到自訂。"""

from tests.conftest import make_market_budget_config, make_student


def test_market_budget_student_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
    )
    default = client.get(
        "/api/games/MarketShoppingBudgetMode/materials/default", headers=auth_headers
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []


def test_market_budget_student_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_put")
    payload = make_market_budget_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["items"] == payload["items"]
    assert saved.json()["budget"] == payload["budget"]
    assert saved.json()["prices"] == payload["prices"]
    assert not saved.json().get("basketOrder")
    assert saved.json()["Start_NPC_Name"] == payload["Start_NPC_Name"]
    assert saved.json()["Start_Dialogues"] == payload["Start_Dialogues"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
    )
    default = client.get(
        "/api/games/MarketShoppingBudgetMode/materials/default", headers=auth_headers
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]
