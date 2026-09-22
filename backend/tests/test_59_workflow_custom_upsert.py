"""測試 59：同一位學生再 PUT，是更新不是再插入一列。"""

from tests.conftest import SIX_GAMES_REVERSED, make_student, saved_workflow_games

SECOND = [
    {"game": "MarketShopping", "order": 1},
    {"game": "MemoryMatch", "order": 2},
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
    {"game": "MarketShoppingBudgetMode", "order": 6},
]


def test_student_workflow_put_twice_keeps_latest(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_upsert")
    first = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SIX_GAMES_REVERSED),
    )
    second = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(SECOND),
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json() == saved_workflow_games(SECOND)

    loaded = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    assert loaded.json() == saved_workflow_games(SECOND)
