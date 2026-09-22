"""測試 158：同一遊戲兩次 POST 成兩列與兩個 id.json。旁邊的扁平檔不被覆蓋。"""

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


def test_two_posts_leave_flat_file(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_two_cfg")
    payload = make_memory_config(client, auth_headers, npc_name="新的一筆")
    flat_body = dict(payload)
    flat_body["Start_NPC_Name"] = "扁平舊檔"
    relative = (
        f"GameMaterialCustomization/{test_teacher['username']}/"
        f"{student['username']}/MemoryMatch.json"
    )
    flat_path = STORAGE_DIR / relative
    flat_path.parent.mkdir(parents=True, exist_ok=True)
    flat_path.write_text(
        json.dumps(flat_body, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = flat_path.read_bytes()
    flat_id = _insert_row(int(test_teacher["id"]), int(student["id"]), "MemoryMatch", relative)

    first_body = dict(payload)
    first_body["Start_NPC_Name"] = "第一份"
    second_body = dict(payload)
    second_body["Start_NPC_Name"] = "第二份"
    url = f"/api/students/{student['id']}/games/MemoryMatch/materials"
    first = client.post(url, headers=auth_headers, json=first_body)
    second = client.post(url, headers=auth_headers, json=second_body)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]

    for saved, npc_name in ((first, "第一份"), (second, "第二份")):
        config_id = saved.json()["id"]
        file_path = flat_path.parent / "MemoryMatch" / f"{config_id}.json"
        assert file_path.is_file()
        assert saved.json()["json_path"].replace("\\", "/").endswith(
            f"/MemoryMatch/{config_id}.json"
        )
        on_disk = json.loads(file_path.read_text(encoding="utf-8"))
        assert "id" not in on_disk
        assert "json_path" not in on_disk
        assert on_disk["Start_NPC_Name"] == npc_name

    assert flat_path.read_bytes() == before
    listed = client.get(url, headers=auth_headers)
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert [item["id"] for item in rows] == sorted(item["id"] for item in rows)
    assert {item["id"] for item in rows} == {flat_id, first.json()["id"], second.json()["id"]}
    flat = next(item for item in rows if item["id"] == flat_id)
    assert flat["json_path"].replace("\\", "/").endswith("/MemoryMatch.json")
    assert flat["Start_NPC_Name"] == "扁平舊檔"
