"""測試 50：PUT 之後 GET 讀到自訂。不再等於 Default。"""

from tests.conftest import SIX_GAMES_REVERSED, make_student, saved_workflow_games


def test_student_workflow_put_then_get(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_put")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert saved.status_code == 200, saved.text
    assert saved.json() == saved_workflow_games(SIX_GAMES_REVERSED)

    loaded = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    default = client.get("/api/workflow/default", headers=auth_headers)
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == saved_workflow_games(SIX_GAMES_REVERSED)
    assert loaded.json() != default.json()
