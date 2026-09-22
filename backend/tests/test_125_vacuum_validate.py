"""測試 125：配對吸塵 5 格與主題規則。不完整或放錯主題會 400。"""

from tests.conftest import make_student, make_tag, make_vacuum_config


def test_vacuum_incomplete_items_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_short")
    payload = make_vacuum_config(client, auth_headers)
    payload["items"] = {"slot_1": payload["items"]["slot_1"]}
    response = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "必須正好填滿 5 個格子"


def test_vacuum_duplicate_material_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_dup")
    payload = make_vacuum_config(client, auth_headers)
    payload["items"]["slot_2"] = payload["items"]["slot_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "同一個素材不能出現兩次"


def test_vacuum_slot_from_other_tag_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_theme")
    payload = make_vacuum_config(client, auth_headers)
    other_tag = make_tag(client, auth_headers, game_code="PairVacuum", name="zz_pytest_吸塵其他")
    extra = client.post(
        f"/api/tags/{other_tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_吸塵錯格"},
    )
    assert extra.status_code == 201, extra.text
    payload["items"]["slot_1"] = extra.json()["code"]
    response = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "正確格必須來自選定主題"


def test_vacuum_empty_npc_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_npc")
    payload = make_vacuum_config(client, auth_headers, npc_name="  ", dialogues=["", "  "])
    response = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["Start_NPC_Name"] == ""
    assert response.json()["Start_Dialogues"] == []
