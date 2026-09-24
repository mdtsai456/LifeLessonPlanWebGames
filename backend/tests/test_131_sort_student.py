"""測試 131：分類推物 PUT/GET。測試四主題規則。測試桶格規則。"""

from tests.conftest import make_sort_config, make_student


def test_sort_student_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/SortArena/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []


def test_sort_student_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_put")
    payload = make_sort_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["tags"] == payload["tags"]
    assert saved.json()["items"] == payload["items"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/SortArena/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]


def test_sort_incomplete_items_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_short")
    payload = make_sort_config(client, auth_headers)
    payload["items"] = {"bin_1_1": payload["items"]["bin_1_1"]}
    response = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "必須正好填滿 20 個格子"


def test_sort_duplicate_material_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_dup")
    payload = make_sort_config(client, auth_headers)
    payload["items"]["bin_1_2"] = payload["items"]["bin_1_1"]
    response = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "同一個素材不能出現兩次"


def test_sort_slot_from_wrong_bin_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_bin")
    payload = make_sort_config(client, auth_headers)
    first = payload["items"]["bin_1_1"]
    payload["items"]["bin_1_1"] = payload["items"]["bin_2_1"]
    payload["items"]["bin_2_1"] = first
    response = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "這個格子只能放對應主題的素材"


def test_sort_not_four_tags_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_tags")
    payload = make_sort_config(client, auth_headers)
    payload["tags"] = payload["tags"][:3]
    response = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "請選擇剛好 4 個主題"


def test_sort_empty_npc_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_npc")
    payload = make_sort_config(client, auth_headers, npc_name="  ", dialogues=["", "  "])
    response = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    assert response.json()["Start_NPC_Name"] == ""
    assert response.json()["Start_Dialogues"] == []
