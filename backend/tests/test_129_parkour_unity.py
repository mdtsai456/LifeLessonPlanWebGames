"""測試 129：Unity 讀決策跑酷。給 rows 不給平鋪 slots。"""

from tests.conftest import UNITY_TEST_KEY, make_parkour_config, make_student


def test_unity_parkour_uses_default_rows(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_ud")
    default = client.get(
        "/api/games/DecisionParkour/materials/default", headers=auth_headers
    ).json()
    response = client.get(
        f"/api/unity/students/{student['id']}/games/DecisionParkour",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "DecisionParkour"
    assert body["studentName"] == student["username"]
    assert body["theme"]["code"] == default["tag"]
    assert "slots" not in body
    assert len(body["rows"]) == 6
    first = body["rows"][0]
    assert set(first) == {"question", "distractor_1", "distractor_2"}
    assert first["question"]["imageUrl"] == default["items"]["theme_1"]
    assert first["distractor_1"]["imageUrl"] == default["items"]["distractor_1"]
    assert first["distractor_2"]["imageUrl"] == default["items"]["distractor_2"]
    assert body["rows"][1]["question"]["imageUrl"] == default["items"]["theme_2"]
    assert body["rows"][1]["distractor_1"]["imageUrl"] == default["items"]["distractor_3"]
    assert body["rows"][1]["distractor_2"]["imageUrl"] == default["items"]["distractor_4"]
    assert body["Start_NPC_Name"] == default["Start_NPC_Name"]
    assert body["Start_Dialogues"] == default["Start_Dialogues"]


def test_unity_parkour_uses_custom_rows(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pk_uc")
    payload = make_parkour_config(client, auth_headers, npc_name="店員", dialogues=["開始跑"])
    saved = client.post(
        f"/api/students/{student['id']}/games/DecisionParkour/materials",
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
    assert "slots" not in body
    assert body["theme"]["code"] == payload["tag"]
    assert body["rows"][0]["question"]["imageUrl"] == payload["items"]["theme_1"]
    assert body["rows"][5]["question"]["imageUrl"] == payload["items"]["theme_6"]
    assert body["rows"][5]["distractor_1"]["imageUrl"] == payload["items"]["distractor_11"]
    assert body["rows"][5]["distractor_2"]["imageUrl"] == payload["items"]["distractor_12"]
    assert body["Start_NPC_Name"] == "店員"
    assert body["Start_Dialogues"] == ["開始跑"]
