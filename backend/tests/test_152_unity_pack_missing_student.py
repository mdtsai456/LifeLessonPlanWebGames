"""測試 152：Unity 一次全量缺學生回 404。"""

from tests.conftest import UNITY_TEST_KEY


def test_unity_pack_missing_student_is_404(client):
    response = client.get(
        "/api/unity/students/999999999",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 404
