"""測試 126：Unity 讀配對吸塵。沒自訂用 Default，有自訂用自訂。"""

from tests.conftest import UNITY_TEST_KEY, make_student, make_vacuum_config


def test_unity_vacuum_uses_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_ud")
    default = client.get("/api/games/PairVacuum/materials/default", headers=auth_headers).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/PairVacuum",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "PairVacuum"
    assert body["studentName"] == student["username"]
    assert body["theme"]["code"] == default["tag"]
    assert body["theme"]["name"]
    assert set(body["slots"]) == set(default["items"])
    assert body["slots"]["slot_1"]["code"] in default["items"]["slot_1"]
    assert body["slots"]["slot_1"]["name"]
    assert body["slots"]["slot_1"]["imageUrl"] == default["items"]["slot_1"]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]


def test_unity_vacuum_uses_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_uc")
    payload = make_vacuum_config(client, auth_headers, npc_name="店員", dialogues=["開始吸"])
    saved = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
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
    assert body["slots"]["slot_1"]["code"] in payload["items"]["slot_1"]
    assert body["slots"]["slot_1"]["imageUrl"] == payload["items"]["slot_1"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始吸"]
