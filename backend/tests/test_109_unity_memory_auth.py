"""測試 109：Unity 讀記憶配對要 X-Unity-Key。"""

from tests.conftest import UNITY_TEST_KEY, make_student


def test_unity_memory_needs_key(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_uk")
    response = client.get(f"/api/unity/students/{student['id']}/games/MemoryMatch")
    assert response.status_code == 401


def test_unity_memory_wrong_key_is_401(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_uk2")
    response = client.get(
        f"/api/unity/students/{student['id']}/games/MemoryMatch",
        headers={"X-Unity-Key": "wrong-key-value"},
    )
    assert response.status_code == 401


def test_unity_memory_ok_with_key(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_uk3")
    response = client.get(
        f"/api/unity/students/{student['id']}/games/MemoryMatch",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 200, response.text
