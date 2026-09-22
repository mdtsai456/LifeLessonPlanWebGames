"""測試 62：PUT 多帶的欄位不會寫進自訂檔。結束對話沒傳時寫成空。"""

from tests.conftest import make_student

SAVED_KEYS = {"game", "gameMaterialCustomizationId", "order", "endNpcName", "endDialogues"}


def test_student_workflow_put_strips_extra_fields(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_strip")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json={
            "startNpcName": "",
            "startDialogues": [],
            "extra": "不要留下",
            "storylines": [
                {
                    "name": "預設",
                    "order": 1,
                    "note": "不要留下",
                    "steps": [
                        {"game": "MarketShopping", "order": 1, "configId": 99},
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
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == {"startNpcName", "startDialogues", "storylines"}
    line = body["storylines"][0]
    assert set(line.keys()) == {"name", "order", "steps"}
    for item in line["steps"]:
        assert set(item.keys()) == SAVED_KEYS
        assert "configId" not in item
        assert item["gameMaterialCustomizationId"] is None
        assert item["endNpcName"] == ""
        assert item["endDialogues"] == []
