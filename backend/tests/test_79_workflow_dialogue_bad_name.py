"""測試 79：NPC 名字不是字串時回 422。"""

from tests.conftest import make_student, workflow_body

GAMES = [
    {"game": "MarketShopping", "order": 1, "endNpcName": 12},
    {"game": "MemoryMatch", "order": 2},
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
]


def test_student_workflow_bad_npc_name_type_is_422(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_npc")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert response.status_code == 422, response.text
