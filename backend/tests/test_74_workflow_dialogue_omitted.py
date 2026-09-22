"""測試 74：沒傳結束對話時，寫成空字串與空陣列。"""

from tests.conftest import SIX_GAMES_REVERSED, make_student, saved_workflow_games


def test_student_workflow_omitted_dialogue_is_empty(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_omit")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    assert response.status_code == 200, response.text
    assert response.json() == saved_workflow_games(SIX_GAMES_REVERSED)
    for item in response.json()["storylines"][0]["steps"]:
        assert item["endNpcName"] == ""
        assert item["endDialogues"] == []
