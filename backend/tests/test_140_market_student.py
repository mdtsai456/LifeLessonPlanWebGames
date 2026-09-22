"""測試 140：超市購物沒自訂退回 Default；PUT 後 GET 讀到自訂。"""

from backend.database import connect_db
from tests.conftest import make_market_shopping_config, make_student


def test_market_student_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/MarketShopping/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []


def test_market_student_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_put")
    payload = make_market_shopping_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["items"] == payload["items"]
    assert saved.json()["basketOrder"] == payload["basketOrder"]
    assert saved.json()["prices"] == payload["prices"]
    assert saved.json()["Start_NPC_Name"] == payload["Start_NPC_Name"]
    assert saved.json()["Start_Dialogues"] == payload["Start_Dialogues"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/MarketShopping/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]


def test_market_student_put_upserts(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_up")
    first = make_market_shopping_config(client, auth_headers, npc_name="第一")
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=first,
    )
    assert saved.status_code == 201, saved.text
    first["Start_NPC_Name"] = "第二"
    again = client.put(
        f"/api/students/{student['id']}/games/MarketShopping/materials/{saved.json()['id']}",
        headers=auth_headers,
        json=first,
    )
    assert again.status_code == 200, again.text
    assert again.json()["Start_NPC_Name"] == "第二"

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS n FROM GameMaterialCustomization
                WHERE student_id = %s
                """,
                (student["id"],),
            )
            assert cursor.fetchone()["n"] == 1
    finally:
        connection.close()


def test_market_duplicate_on_shelf_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_dup")
    payload = make_market_shopping_config(client, auth_headers)
    payload["items"]["shelf_regular_2"] = payload["items"]["shelf_regular_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["items"]["shelf_regular_2"] == payload["items"]["shelf_regular_1"]


def test_market_empty_npc_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_npc")
    payload = make_market_shopping_config(
        client, auth_headers, npc_name="  ", dialogues=["", "  "]
    )
    response = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["Start_NPC_Name"] == ""
    assert response.json()["Start_Dialogues"] == []
