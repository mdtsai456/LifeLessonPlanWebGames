"""測試 76：結束對白不是字串陣列時回 422。"""

from tests.conftest import make_student, workflow_body

GAMES = [
    {"game": "MarketShopping", "order": 1},
    {"game": "MemoryMatch", "order": 2, "endDialogues": "不是陣列"},
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
]


def test_student_workflow_bad_dialogue_type_is_422(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_bad")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert response.status_code == 422, response.text
