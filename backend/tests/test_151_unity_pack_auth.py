"""測試 151：Unity 一次全量要 X-Unity-Key。"""

from tests.conftest import make_student


def test_unity_pack_needs_key(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_uk")
    response = client.get(f"/api/unity/students/{student['id']}")
    assert response.status_code == 401


def test_unity_pack_wrong_key_is_401(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_uk2")
    response = client.get(
        f"/api/unity/students/{student['id']}",
        headers={"X-Unity-Key": "wrong-key-value"},
    )
    assert response.status_code == 401


def test_unity_pack_empty_key_is_401(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_uk3")
    response = client.get(
        f"/api/unity/students/{student['id']}",
        headers={"X-Unity-Key": ""},
    )
    assert response.status_code == 401
