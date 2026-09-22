"""測試 132：Unity 讀分類推物。給 themes 與 20 個 slots。"""

from tests.conftest import UNITY_TEST_KEY, make_sort_config, make_student


def test_unity_sort_uses_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_ud")
    default = client.get("/api/games/SortArena/materials/default", headers=auth_headers).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/SortArena",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "SortArena"
    assert body["studentName"] == student["username"]
    assert [row["code"] for row in body["themes"]] == default["tags"]
    assert all(row["name"] for row in body["themes"])
    assert set(body["slots"]) == set(default["items"])
    assert body["slots"]["bin_1_1"]["code"] in default["items"]["bin_1_1"]
    assert body["slots"]["bin_1_1"]["imageUrl"] == default["items"]["bin_1_1"]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]


def test_unity_sort_uses_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_sort_uc")
    payload = make_sort_config(client, auth_headers, npc_name="店員", dialogues=["開始推"])
    saved = client.post(
        f"/api/students/{student['id']}/games/SortArena/materials",
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
    assert [row["code"] for row in body["themes"]] == payload["tags"]
    assert body["slots"]["bin_1_1"]["imageUrl"] == payload["items"]["bin_1_1"]
    assert body["slots"]["bin_4_5"]["imageUrl"] == payload["items"]["bin_4_5"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始推"]
