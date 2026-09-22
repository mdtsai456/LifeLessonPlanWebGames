"""測試 51：其他老師讀不到，也改不了這位學生的關卡。"""

from tests.conftest import SIX_GAMES_REVERSED, make_student, saved_workflow_games


def test_other_teacher_cannot_get_student_workflow(
    client, auth_headers, other_auth_headers
):
    student = make_student(client, auth_headers, "zz_pytest_student_secret")
    response = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=other_auth_headers,
    )
    assert response.status_code == 404


def test_other_teacher_cannot_put_student_workflow(
    client, auth_headers, other_auth_headers
):
    student = make_student(client, auth_headers, "zz_pytest_student_locked")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=other_auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert response.status_code == 404
