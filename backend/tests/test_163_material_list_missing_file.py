"""測試 163：清單略過檔不在的列。PUT 仍把刪掉的 JSON 寫回原路徑。"""

import json

from backend.database import connect_db
from tests.conftest import STORAGE_DIR, make_memory_config, make_student


def _insert_row(teacher_id: int, student_id: int, game_code: str, relative: str) -> int:
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


def _row_count(student_id: int) -> int:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS n FROM GameMaterialCustomization WHERE student_id = %s",
                (student_id,),
            )
            return int(cursor.fetchone()["n"])
    finally:
        connection.close()


def _row_still_there(config_id: int) -> bool:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM GameMaterialCustomization WHERE id = %s",
                (config_id,),
            )
            return cursor.fetchone() is not None
    finally:
        connection.close()


def test_missing_only_row_lists_empty(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_miss_only")
    relative = (
        f"GameMaterialCustomization/{test_teacher['username']}/"
        f"{student['username']}/MemoryMatch/missing.json"
    )
    config_id = _insert_row(
        int(test_teacher["id"]), int(student["id"]), "MemoryMatch", relative
    )
    assert not (STORAGE_DIR / relative).is_file()
    listed = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert listed.status_code == 200, listed.text
    assert listed.json() == []
    assert _row_still_there(config_id)


def test_list_keeps_row_whose_file_exists(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_miss_one")
    payload = make_memory_config(client, auth_headers, npc_name="還在")
    url = f"/api/students/{student['id']}/games/MemoryMatch/materials"
    saved = client.post(url, headers=auth_headers, json=payload)
    assert saved.status_code == 201, saved.text
    kept_id = saved.json()["id"]
    missing = (
        f"GameMaterialCustomization/{test_teacher['username']}/"
        f"{student['username']}/MemoryMatch/gone.json"
    )
    _insert_row(int(test_teacher["id"]), int(student["id"]), "MemoryMatch", missing)
    listed = client.get(url, headers=auth_headers)
    assert listed.status_code == 200, listed.text
    assert [item["id"] for item in listed.json()] == [kept_id]


def test_put_rewrites_deleted_json(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_miss_put")
    payload = make_memory_config(client, auth_headers, npc_name="原本")
    url = f"/api/students/{student['id']}/games/MemoryMatch/materials"
    saved = client.post(url, headers=auth_headers, json=payload)
    assert saved.status_code == 201, saved.text
    config_id = saved.json()["id"]
    relative = saved.json()["json_path"]
    before = _row_count(int(student["id"]))
    file_path = STORAGE_DIR / relative
    file_path.unlink()
    payload["Start_NPC_Name"] = "寫回"
    updated = client.put(f"{url}/{config_id}", headers=auth_headers, json=payload)
    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == config_id
    assert updated.json()["json_path"] == relative
    assert updated.json()["Start_NPC_Name"] == "寫回"
    assert _row_count(int(student["id"])) == before
    on_disk = json.loads(file_path.read_text(encoding="utf-8"))
    assert on_disk["Start_NPC_Name"] == "寫回"
