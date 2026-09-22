"""測試 159：PUT 寫回原路徑。扁平舊列不寫入 id.json。寫檔失敗時不保留該列。不帶 id 的 PUT 回 405。"""

import json
from pathlib import Path

import pytest
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


def test_put_writes_existing_json_path(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_put_path")
    payload = make_memory_config(client, auth_headers, npc_name="原本")
    url = f"/api/students/{student['id']}/games/MemoryMatch/materials"
    saved = client.post(url, headers=auth_headers, json=payload)
    assert saved.status_code == 201, saved.text
    config_id = saved.json()["id"]
    relative = saved.json()["json_path"]
    payload["Start_NPC_Name"] = "改過"
    updated = client.put(f"{url}/{config_id}", headers=auth_headers, json=payload)
    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == config_id
    assert updated.json()["json_path"] == relative
    assert updated.json()["Start_NPC_Name"] == "改過"
    on_disk = json.loads((STORAGE_DIR / relative).read_text(encoding="utf-8"))
    assert on_disk["Start_NPC_Name"] == "改過"
    game_dir = (
        STORAGE_DIR
        / "GameMaterialCustomization"
        / test_teacher["username"]
        / student["username"]
        / "MemoryMatch"
    )
    assert [path.name for path in game_dir.glob("*.json")] == [f"{config_id}.json"]


def test_put_flat_row_stays_flat(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_put_flat")
    payload = make_memory_config(client, auth_headers, npc_name="扁平原本")
    relative = (
        f"GameMaterialCustomization/{test_teacher['username']}/"
        f"{student['username']}/MemoryMatch.json"
    )
    flat_path = STORAGE_DIR / relative
    flat_path.parent.mkdir(parents=True, exist_ok=True)
    flat_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    config_id = _insert_row(int(test_teacher["id"]), int(student["id"]), "MemoryMatch", relative)
    payload["Start_NPC_Name"] = "扁平改過"
    updated = client.put(
        f"/api/students/{student['id']}/games/MemoryMatch/materials/{config_id}",
        headers=auth_headers,
        json=payload,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["json_path"].replace("\\", "/").endswith("/MemoryMatch.json")
    moved = flat_path.parent / "MemoryMatch" / f"{config_id}.json"
    assert not moved.is_file()
    on_disk = json.loads(flat_path.read_text(encoding="utf-8"))
    assert on_disk["Start_NPC_Name"] == "扁平改過"


def test_failed_write_leaves_no_row(client, auth_headers, monkeypatch):
    student = make_student(client, auth_headers, "zz_pytest_student_put_fail")
    payload = make_memory_config(client, auth_headers)

    def fail(self, *args, **kwargs):
        raise OSError("zz_pytest_write_fail")

    monkeypatch.setattr(Path, "write_text", fail)
    with pytest.raises(OSError, match="zz_pytest_write_fail"):
        client.post(
            f"/api/students/{student['id']}/games/MemoryMatch/materials",
            headers=auth_headers,
            json=payload,
        )
    assert _row_count(int(student["id"])) == 0


def test_put_without_id_is_405(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_put_405")
    payload = make_memory_config(client, auth_headers)
    response = client.put(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 405
