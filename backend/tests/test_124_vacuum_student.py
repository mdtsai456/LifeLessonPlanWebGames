"""測試 124：配對吸塵沒自訂退回 Default；PUT 後 GET 讀到自訂。"""

from tests.conftest import make_student, make_vacuum_config


def test_vacuum_student_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/PairVacuum/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []


def test_vacuum_student_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_vac_put")
    payload = make_vacuum_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["tag"] == payload["tag"]
    assert saved.json()["items"] == payload["items"]
    assert saved.json()["Start_NPC_Name"] == payload["Start_NPC_Name"]
    assert saved.json()["Start_Dialogues"] == payload["Start_Dialogues"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/PairVacuum/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]
