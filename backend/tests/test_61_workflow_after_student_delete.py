"""測試 61：學生刪除之後，關卡 API 也找不到該學生。"""

from tests.conftest import SIX_GAMES_REVERSED, make_student, saved_workflow_games


def test_deleted_student_workflow_is_404(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_afterdel")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert saved.status_code == 200, saved.text

    deleted = client.delete(f"/api/students/{student['id']}", headers=auth_headers)
    assert deleted.status_code == 200, deleted.text

    response = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    assert response.status_code == 404
