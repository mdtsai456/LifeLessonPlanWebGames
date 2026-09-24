"""測試 161：Unity 整包沒有頂層 games。舊 games 檔只在記憶體編成預設。舊 games 檔只綁扁平列。"""

import json

from backend.database import connect_db
from tests.conftest import STORAGE_DIR, UNITY_TEST_KEY, make_memory_config, make_student


def _insert_material(teacher_id: int, student_id: int, game_code: str, relative: str) -> int:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM Game WHERE game_code = %s", (game_code,))
            game_id = cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO GameMaterialCustomization
                    (teacher_id, student_id, game_id, json_path)
                VALUES (%s, %s, %s, %s)
                """,
                (teacher_id, student_id, game_id, relative),
            )
            config_id = int(cursor.lastrowid)
        connection.commit()
    finally:
        connection.close()
    return config_id


def _write_legacy_workflow(teacher: dict, student: dict, legacy: dict) -> tuple[object, bytes]:
    relative = (
        f"GameWorkflowCustomization/{teacher['username']}/{student['username']}/workflow.json"
    )
    path = STORAGE_DIR / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO GameWorkflowCustomization (teacher_id, student_id, json_path)
                VALUES (%s, %s, %s)
                """,
                (teacher["id"], student["id"], relative),
            )
        connection.commit()
    finally:
        connection.close()
    return path, path.read_bytes()


def test_pack_steps_carry_material(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_mat")
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    response = client.get(f"/api/unity/students/{student['id']}", headers=unity_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"studentName", "workflow"}
    assert "games" not in body
    steps = body["workflow"]["storylines"][0]["steps"]
    assert steps
    for step in steps:
        assert "material" in step
        assert step["material"]["game"] == step["game"]
        assert step["material"]["studentName"] == student["username"]


def test_legacy_games_bind_only_flat_row(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_flat")
    shared = make_memory_config(client, auth_headers, npc_name="扁平列", dialogues=["舊檔"])
    flat_payload = dict(shared)
    relative = (
        f"GameMaterialCustomization/{test_teacher['username']}/"
        f"{student['username']}/MemoryMatch.json"
    )
    flat_path = STORAGE_DIR / relative
    flat_path.parent.mkdir(parents=True, exist_ok=True)
    flat_path.write_text(
        json.dumps(flat_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    flat_id = _insert_material(
        int(test_teacher["id"]), int(student["id"]), "MemoryMatch", relative
    )
    posted_payload = dict(shared)
    posted_payload["Start_NPC_Name"] = "新檔"
    posted_payload["Start_Dialogues"] = ["不要自動選"]
    posted = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=posted_payload,
    )
    assert posted.status_code == 201, posted.text
    legacy = {
        "games": [
            {
                "game": "MemoryMatch",
                "order": 1,
                "endNpcName": "結束",
                "endDialogues": ["這一關"],
            },
            {
                "game": "PairVacuum",
                "order": 2,
                "endNpcName": "",
                "endDialogues": [],
            },
        ]
    }
    path, before = _write_legacy_workflow(test_teacher, student, legacy)
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    response = client.get(f"/api/unity/students/{student['id']}", headers=unity_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "games" not in body
    workflow = body["workflow"]
    assert workflow["startNpcName"] == ""
    assert workflow["startDialogues"] == []
    assert workflow["storylines"][0]["name"] == "預設"
    steps = {item["game"]: item for item in workflow["storylines"][0]["steps"]}
    assert steps["MemoryMatch"]["gameMaterialCustomizationId"] == flat_id
    assert steps["MemoryMatch"]["gameMaterialCustomizationId"] != posted.json()["id"]
    assert steps["MemoryMatch"]["endNpcName"] == "結束"
    assert steps["MemoryMatch"]["material"]["Start_NPC_Name"] == "扁平列"
    assert steps["PairVacuum"]["gameMaterialCustomizationId"] is None
    default_vacuum = client.get(
        f"/api/unity/students/{student['id']}/games/PairVacuum",
        headers=unity_headers,
    )
    assert default_vacuum.status_code == 200, default_vacuum.text
    assert steps["PairVacuum"]["material"] == default_vacuum.json()
    assert path.read_bytes() == before


def test_multiple_flat_rows_bind_null(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_flats")
    payload = make_memory_config(client, auth_headers, npc_name="不要任選")
    teacher_name = test_teacher["username"]
    student_name = student["username"]
    first_relative = f"GameMaterialCustomization/{teacher_name}/{student_name}/MemoryMatch.json"
    second_relative = (
        f"GameMaterialCustomization/{teacher_name}/{student_name}/extra/MemoryMatch.json"
    )
    for relative in (first_relative, second_relative):
        path = STORAGE_DIR / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _insert_material(int(test_teacher["id"]), int(student["id"]), "MemoryMatch", relative)
    legacy = {
        "games": [
            {"game": "MemoryMatch", "order": 1, "endNpcName": "", "endDialogues": []},
        ]
    }
    _write_legacy_workflow(test_teacher, student, legacy)
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    response = client.get(f"/api/unity/students/{student['id']}", headers=unity_headers)
    assert response.status_code == 200, response.text
    step = response.json()["workflow"]["storylines"][0]["steps"][0]
    assert step["gameMaterialCustomizationId"] is None
    default_play = client.get(
        "/api/games/MemoryMatch/materials/default",
        headers=auth_headers,
    )
    assert step["material"]["Start_NPC_Name"] == default_play.json()["Start_NPC_Name"]
    assert step["material"]["Start_NPC_Name"] != "不要任選"


def test_material_config_returns_owned_play_json(client, auth_headers, other_auth_headers):
    owner = make_student(client, auth_headers, "zz_pytest_student_pack_cfg")
    other = make_student(client, other_auth_headers, "zz_pytest_student_pack_other")
    payload = make_memory_config(client, auth_headers, npc_name="這一筆", dialogues=["開始"])
    saved = client.post(
        f"/api/students/{owner['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    config_id = saved.json()["id"]
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    loaded = client.get(
        f"/api/unity/students/{owner['id']}/material-configs/{config_id}",
        headers=unity_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["studentName"] == owner["username"]
    assert loaded.json()["Start_NPC_Name"] == "這一筆"
    assert loaded.json()["theme"]["code"] == payload["tag"]
    foreign = client.get(
        f"/api/unity/students/{other['id']}/material-configs/{config_id}",
        headers=unity_headers,
    )
    assert foreign.status_code == 404
    missing = client.get(
        f"/api/unity/students/{owner['id']}/material-configs/999999999",
        headers=unity_headers,
    )
    assert missing.status_code == 404


def test_old_game_url_rejects_id_file_and_many_rows(client, auth_headers):
    one = make_student(client, auth_headers, "zz_pytest_student_pack_one")
    payload = make_memory_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{one['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    only_id = client.get(
        f"/api/unity/students/{one['id']}/games/MemoryMatch",
        headers=unity_headers,
    )
    assert only_id.status_code == 400

    many = make_student(client, auth_headers, "zz_pytest_student_pack_many")
    for npc_name in ("甲", "乙"):
        body = dict(payload)
        body["Start_NPC_Name"] = npc_name
        created = client.post(
            f"/api/students/{many['id']}/games/MemoryMatch/materials",
            headers=auth_headers,
            json=body,
        )
        assert created.status_code == 201, created.text
    multiple = client.get(
        f"/api/unity/students/{many['id']}/games/MemoryMatch",
        headers=unity_headers,
    )
    assert multiple.status_code == 400
