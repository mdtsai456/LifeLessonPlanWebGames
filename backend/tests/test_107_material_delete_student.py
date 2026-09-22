"""測試 107：刪除學生時一併刪除自訂素材 JSON。"""

from tests.conftest import STORAGE_DIR, make_memory_config, make_student


def test_deleted_student_material_file_is_gone(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_gone")
    payload = make_memory_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text

    path = (
        STORAGE_DIR
        / "GameMaterialCustomization"
        / test_teacher["username"]
        / student["username"]
        / "MemoryMatch"
        / f"{saved.json()['id']}.json"
    )
    assert path.is_file()

    deleted = client.delete(f"/api/students/{student['id']}", headers=auth_headers)
    assert deleted.status_code == 200, deleted.text
    assert not path.is_file()
    assert not path.parents[1].is_dir()
