"""測試 111：有自訂時 Unity 用 material-configs 讀該筆。有自訂時 Unity 不讀 Default。"""

from tests.conftest import UNITY_TEST_KEY, make_memory_config, make_student


def test_unity_memory_uses_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_uc")
    payload = make_memory_config(client, auth_headers, npc_name="店員", dialogues=["開始吧"])
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
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
    assert body["studentName"] == student["username"]
    assert body["theme"]["code"] == payload["tag"]
    assert payload["items"]["theme_1"].startswith("/static/")
    assert body["slots"]["theme_1"]["code"] in payload["items"]["theme_1"]
    assert body["slots"]["theme_1"]["imageUrl"] == payload["items"]["theme_1"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始吧"]
