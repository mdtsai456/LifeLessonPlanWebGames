"""測試 105：9 格與主題規則。不完整或放錯主題會 400。"""

from tests.conftest import make_memory_config, make_student


def test_incomplete_items_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_short")
    payload = make_memory_config(client, auth_headers)
    payload["items"] = {"theme_1": payload["items"]["theme_1"]}
    response = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "必須正好填滿 9 個格子"


def test_duplicate_material_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_dup")
    payload = make_memory_config(client, auth_headers)
    payload["items"]["theme_2"] = payload["items"]["theme_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "同一個素材不能出現兩次"


def test_theme_slot_from_other_tag_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_theme")
    payload = make_memory_config(client, auth_headers)
    theme_code = payload["items"]["theme_1"]
    payload["items"]["theme_1"] = payload["items"]["distractor_1"]
    payload["items"]["distractor_1"] = theme_code
    response = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "正確格必須來自選定主題"


def test_distractor_from_theme_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_ng")
    payload = make_memory_config(client, auth_headers)
    extra = client.post(
        f"/api/tags/{payload['tag']}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_多一個正確"},
    )
    assert extra.status_code == 201, extra.text
    payload["items"]["distractor_1"] = extra.json()["code"]
    response = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "錯誤格不能放選定主題的素材"


def test_empty_npc_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_npc")
    payload = make_memory_config(client, auth_headers, npc_name="  ", dialogues=["", "  "])
    response = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["Start_NPC_Name"] == ""
    assert response.json()["Start_Dialogues"] == []
