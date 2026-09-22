"""測試 103：沒自訂時學生 GET 是空陣列。"""

from tests.conftest import make_student


def test_student_material_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_fb")
    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == []
