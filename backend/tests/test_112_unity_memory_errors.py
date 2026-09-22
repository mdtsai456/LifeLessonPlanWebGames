"""測試 112：Unity 未知遊戲 400。缺學生 404。"""

from tests.conftest import UNITY_TEST_KEY, make_student


def test_unity_unknown_game_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_ug")
    response = client.get(
        f"/api/unity/students/{student['id']}/games/UnknownGame",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "此遊戲配置尚未提供"


def test_unity_missing_student_is_404(client):
    response = client.get(
        "/api/unity/students/999999999/games/MemoryMatch",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 404
