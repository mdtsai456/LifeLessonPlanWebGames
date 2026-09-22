"""測試 52：學生不存在時，關卡 API 回 404。"""


def test_missing_student_workflow_get_is_404(client, auth_headers):
    response = client.get("/api/students/999999999/workflow", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "找不到這位學生"


def test_missing_student_workflow_put_is_404(client, auth_headers):
    response = client.put(
        "/api/students/999999999/workflow",
        headers=auth_headers,
        json={
            "startNpcName": "",
            "startDialogues": [],
            "storylines": [
                {
                    "name": "預設",
                    "order": 1,
                    "steps": [
                        {"game": "MarketShopping", "order": 1},
                        {"game": "MemoryMatch", "order": 2},
                        {"game": "PairVacuum", "order": 3},
                        {"game": "SortArena", "order": 4},
                        {"game": "DecisionParkour", "order": 5},
                        {"game": "MarketShoppingBudgetMode", "order": 6},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "找不到這位學生"
