"""測試 128：決策跑酷 PUT/GET。測試題目主題規則。測試干擾主題規則。"""

from tests.conftest import make_parkour_config, make_student


def test_parkour_student_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/DecisionParkour/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []


def test_parkour_student_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_put")
    payload = make_parkour_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["tag"] == payload["tag"]
    assert saved.json()["items"] == payload["items"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/DecisionParkour/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]


def test_parkour_incomplete_items_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_short")
    payload = make_parkour_config(client, auth_headers)
    payload["items"] = {"theme_1": payload["items"]["theme_1"]}
    response = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "必須正好填滿 18 個格子"


def test_parkour_duplicate_material_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_dup")
    payload = make_parkour_config(client, auth_headers)
    payload["items"]["theme_2"] = payload["items"]["theme_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "同一個素材不能出現兩次"


def test_parkour_theme_slot_from_other_tag_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_theme")
    payload = make_parkour_config(client, auth_headers)
    theme_code = payload["items"]["theme_1"]
    payload["items"]["theme_1"] = payload["items"]["distractor_1"]
    payload["items"]["distractor_1"] = theme_code
    response = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "正確格必須來自選定主題"


def test_parkour_distractor_from_theme_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_ng")
    payload = make_parkour_config(client, auth_headers)
    extra = client.post(
        f"/api/tags/{payload['tag']}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_跑酷多一個正確"},
    )
    assert extra.status_code == 201, extra.text
    payload["items"]["distractor_1"] = extra.json()["code"]
    response = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "錯誤格不能放選定主題的素材"


def test_parkour_empty_npc_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_npc")
    payload = make_parkour_config(client, auth_headers, npc_name="  ", dialogues=["", "  "])
    response = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["Start_NPC_Name"] == ""
    assert response.json()["Start_Dialogues"] == []
