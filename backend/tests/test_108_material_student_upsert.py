"""測試 108：建立使用 POST。同一筆再次儲存使用帶 id 的 PUT。此儲存不新增一列。"""

from backend.database import connect_db
from tests.conftest import make_memory_config, make_student


def test_student_material_put_upserts(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_up")
    first = make_memory_config(client, auth_headers, npc_name="第一")
    second_name = "第二"
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=first,
    )
    assert saved.status_code == 201, saved.text
    first["Start_NPC_Name"] = second_name
    again = client.put(
        f"/api/students/{student['id']}/games/MemoryMatch/materials/{saved.json()['id']}",
        headers=auth_headers,
        json=first,
    )
    assert again.status_code == 200, again.text
    assert again.json()["Start_NPC_Name"] == second_name

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS n FROM GameMaterialCustomization
                WHERE student_id = %s
                """,
                (student["id"],),
            )
            assert cursor.fetchone()["n"] == 1
    finally:
        connection.close()
