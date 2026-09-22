"""測試 75：存檔前去掉前後空白，並刪除空行。"""

from tests.conftest import make_student, storyline_steps, workflow_body

GAMES = [
    {"game": "MarketShopping", "order": 1, "endNpcName": "  ", "endDialogues": ["", "  "]},
    {
        "game": "MemoryMatch",
        "order": 2,
        "endNpcName": "  阿姨  ",
        "endDialogues": ["  你好  ", "", "  ", "下一句"],
    },
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
    {"game": "MarketShoppingBudgetMode", "order": 6, "endNpcName": "", "endDialogues": []},
]


def test_student_workflow_trims_dialogue(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_trim")
    response = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert response.status_code == 200, response.text
    games = {item["game"]: item for item in storyline_steps(response.json())}
    assert games["MarketShopping"]["endNpcName"] == ""
    assert games["MarketShopping"]["endDialogues"] == []
    assert games["MemoryMatch"]["endNpcName"] == "阿姨"
    assert games["MemoryMatch"]["endDialogues"] == ["你好", "下一句"]
    assert games["PairVacuum"]["endNpcName"] == ""
    assert games["PairVacuum"]["endDialogues"] == []
