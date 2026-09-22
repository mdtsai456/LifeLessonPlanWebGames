"""測試 66：刪除學生時一併刪除自訂關卡 JSON。"""

from tests.conftest import SIX_GAMES_REVERSED, STORAGE_DIR, make_student, saved_workflow_games


def test_deleted_student_workflow_file_is_gone(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_filegone")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert saved.status_code == 200, saved.text

    path = (
        STORAGE_DIR
        / "GameWorkflowCustomization"
        / test_teacher["username"]
        / student["username"]
        / "workflow.json"
    )
    assert path.is_file()

    deleted = client.delete(f"/api/students/{student['id']}", headers=auth_headers)
    assert deleted.status_code == 200, deleted.text
    assert not path.is_file()
    assert not path.parent.is_dir()
