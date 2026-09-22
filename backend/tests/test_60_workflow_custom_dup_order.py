"""測試 60：order 重複也回 400。"""

from tests.conftest import make_student, workflow_body


def test_student_workflow_put_duplicate_order_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_duporder")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(
            [
                {"game": "MarketShopping", "order": 1},
                {"game": "MemoryMatch", "order": 1},
                {"game": "PairVacuum", "order": 3},
                {"game": "SortArena", "order": 4},
                {"game": "DecisionParkour", "order": 5},
            ]
        ),
    )
    assert response.status_code == 400
