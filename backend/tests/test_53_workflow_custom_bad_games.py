"""測試 53：少於六款可以儲存。未知遊戲仍回 400。"""

from tests.conftest import make_student, saved_workflow_games, workflow_body

SHORT = [
    {"game": "MarketShopping", "order": 1},
    {"game": "MemoryMatch", "order": 2},
]


def test_student_workflow_put_fewer_games_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_badcount")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SHORT),
    )
    assert response.status_code == 200, response.text
    assert response.json() == saved_workflow_games(SHORT)


def test_student_workflow_put_unknown_game_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_badgame")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(
            [
                {"game": "NotAGame", "order": 1},
                {"game": "MemoryMatch", "order": 2},
                {"game": "PairVacuum", "order": 3},
                {"game": "SortArena", "order": 4},
                {"game": "DecisionParkour", "order": 5},
            ]
        ),
    )
    assert response.status_code == 400
