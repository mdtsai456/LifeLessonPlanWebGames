"""測試 146：Unity 讀預算模式。有 budget。沒有購物清單。"""

from tests.conftest import UNITY_TEST_KEY, make_market_budget_config, make_student


def test_unity_market_budget_uses_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_ud")
    default = client.get(
        "/api/games/MarketShoppingBudgetMode/materials/default", headers=auth_headers
    ).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/MarketShoppingBudgetMode",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MarketShoppingBudgetMode"
    assert body["studentName"] == student["username"]
    assert "theme" not in body
    assert "basketOrder" not in body
    assert isinstance(body["shelves"], list)
    assert len(body["shelves"]) == len(default["items"])
    assert body["budget"] == default["budget"]
    by_slot = {row["slot"]: row for row in body["shelves"]}
    fruit = by_slot["shelf_fruit_1"]
    assert fruit["code"] in default["items"]["shelf_fruit_1"]
    assert fruit["price"] == default["prices"][fruit["code"]]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]


def test_unity_market_budget_uses_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_uc")
    payload = make_market_budget_config(
        client, auth_headers, npc_name="店員", dialogues=["開始買"]
    )
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text

    response = client.get(
        f"/api/unity/students/{student['id']}/material-configs/{saved.json()['id']}",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget"] == payload["budget"]
    assert "basketOrder" not in body
    by_slot = {row["slot"]: row for row in body["shelves"]}
    assert by_slot["shelf_regular_1"]["imageUrl"] == payload["items"]["shelf_regular_1"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始買"]
