"""測試 58：資料庫有自訂列但檔不存在時，仍回傳 Default。"""

from tests.conftest import SIX_GAMES_REVERSED, STORAGE_DIR, TEST_USERNAME, make_student, saved_workflow_games


def test_missing_custom_file_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_missingfile")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert saved.status_code == 200, saved.text

    path = (
        STORAGE_DIR
        / "GameWorkflowCustomization"
        / TEST_USERNAME
        / "zz_pytest_student_missingfile"
        / "workflow.json"
    )
    assert path.is_file()
    path.unlink()

    custom = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    default = client.get("/api/workflow/default", headers=auth_headers)
    assert custom.status_code == 200, custom.text
    assert custom.json() == default.json()
