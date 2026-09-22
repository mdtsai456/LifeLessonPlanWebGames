"""測試 77：只有一關有結束對話。其他關為空。順序不變。"""

from tests.conftest import make_student, storyline_steps, workflow_body

GAMES = [
    {"game": "DecisionParkour", "order": 1, "endNpcName": "", "endDialogues": []},
    {"game": "SortArena", "order": 2, "endNpcName": "", "endDialogues": []},
    {"game": "PairVacuum", "order": 3, "endNpcName": "店員", "endDialogues": ["謝謝", "下一關"]},
    {"game": "MemoryMatch", "order": 4, "endNpcName": "", "endDialogues": []},
    {"game": "MarketShopping", "order": 5, "endNpcName": "", "endDialogues": []},
    {"game": "MarketShoppingBudgetMode", "order": 6, "endNpcName": "", "endDialogues": []},
]


def test_student_workflow_one_game_has_dialogue(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_one")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert response.status_code == 200, response.text
    games = storyline_steps(response.json())
    assert [item["game"] for item in games] == [item["game"] for item in GAMES]
    assert [item["order"] for item in games] == [1, 2, 3, 4, 5, 6]
    vacuum = next(item for item in games if item["game"] == "PairVacuum")
    assert vacuum["order"] == 3
    assert vacuum["endNpcName"] == "店員"
    assert vacuum["endDialogues"] == ["謝謝", "下一關"]
    others = [item for item in games if item["game"] != "PairVacuum"]
    for item in others:
        assert item["endNpcName"] == ""
        assert item["endDialogues"] == []
