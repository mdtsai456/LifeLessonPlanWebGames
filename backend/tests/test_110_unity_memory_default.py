"""測試 110：沒自訂時 Unity 讀 Default 組好的格子與開場。"""

from tests.conftest import UNITY_TEST_KEY, make_student


def test_unity_memory_uses_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_ud")
    default = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/MemoryMatch",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "MemoryMatch"
    assert body["studentName"] == student["username"]
    assert body["theme"]["code"] == default["tag"]
    assert body["theme"]["name"]
    assert set(body["slots"]) == set(default["items"])
    assert default["items"]["theme_1"].startswith("/static/")
    assert body["slots"]["theme_1"]["code"] in default["items"]["theme_1"]
    assert body["slots"]["theme_1"]["name"]
    assert body["slots"]["theme_1"]["imageUrl"] == default["items"]["theme_1"]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]
