"""測試 104：PUT 之後 GET 讀到自訂。不再等於 Default。"""

from tests.conftest import make_memory_config, make_student


def test_student_material_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_put")
    payload = make_memory_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["tag"] == payload["tag"]
    assert saved.json()["items"] == payload["items"]
    assert saved.json()["Start_NPC_Name"] == payload["Start_NPC_Name"]
    assert saved.json()["Start_Dialogues"] == payload["Start_Dialogues"]

    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    default = client.get("/api/games/MemoryMatch/materials/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == [saved.json()]
