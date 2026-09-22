"""測試 106：不能改別人的學生。缺學生 404。"""

from tests.conftest import make_memory_config, make_student


def test_other_teacher_student_material_is_404(client, auth_headers, other_auth_headers):
    student = make_student(client, other_auth_headers, "zz_pytest_student_mat_other")
    payload = make_memory_config(client, auth_headers)
    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 404
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 404


def test_missing_student_material_is_404(client, auth_headers):
    payload = make_memory_config(client, auth_headers)
    response = client.post(
        "/api/students/999999999/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 404
