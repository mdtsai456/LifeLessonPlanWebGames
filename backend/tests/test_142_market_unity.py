"""測試 142：Unity 讀超市購物。組 shelves 與 basketOrder。"""

from tests.conftest import UNITY_TEST_KEY, make_market_shopping_config, make_student


def test_unity_market_uses_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_ud")
    default = client.get(
        "/api/games/MarketShopping/materials/default", headers=auth_headers
    ).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/MarketShopping",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MarketShopping"
    assert body["studentName"] == student["username"]
    assert "theme" not in body
    assert "tag" not in body
    assert isinstance(body["shelves"], list)
    assert len(body["shelves"]) == len(default["items"])
    by_slot = {row["slot"]: row for row in body["shelves"]}
    assert set(by_slot) == set(default["items"])
    fruit = by_slot["shelf_fruit_1"]
    assert fruit["code"] in default["items"]["shelf_fruit_1"]
    assert fruit["name"]
    assert fruit["imageUrl"] == default["items"]["shelf_fruit_1"]
    assert fruit["price"] == default["prices"][fruit["code"]]
    assert [row["code"] for row in body["basketOrder"]] == default["basketOrder"]
    first_basket = body["basketOrder"][0]
    assert first_basket["name"]
    assert first_basket["imageUrl"].startswith("/static/")
    assert first_basket["price"] == default["prices"][first_basket["code"]]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]


def test_unity_market_uses_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_uc")
    payload = make_market_shopping_config(
        client, auth_headers, npc_name="店員", dialogues=["開始拿"]
    )
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
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
    by_slot = {row["slot"]: row for row in body["shelves"]}
    assert by_slot["shelf_regular_1"]["imageUrl"] == payload["items"]["shelf_regular_1"]
    assert [row["code"] for row in body["basketOrder"]] == payload["basketOrder"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始拿"]
