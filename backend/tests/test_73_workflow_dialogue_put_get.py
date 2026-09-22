"""測試 73：寫入結束對話後，GET 讀回相同內容。"""

from tests.conftest import make_student, saved_workflow_games

GAMES = [
    {
        "game": "MarketShopping",
        "order": 1,
        "endNpcName": "",
        "endDialogues": [],
    },
    {
        "game": "MemoryMatch",
        "order": 2,
        "endNpcName": "阿姨",
        "endDialogues": ["這一關完成了,我們回家吧!"],
    },
    {
        "game": "PairVacuum",
        "order": 3,
        "endNpcName": "",
        "endDialogues": [],
    },
    {
        "game": "SortArena",
        "order": 4,
        "endNpcName": "",
        "endDialogues": [],
    },
    {
        "game": "DecisionParkour",
        "order": 5,
        "endNpcName": "",
        "endDialogues": [],
    },
    {
        "game": "MarketShoppingBudgetMode",
        "order": 6,
        "endNpcName": "",
        "endDialogues": [],
    },
]


def test_student_workflow_put_then_get_dialogues(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_put")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(GAMES),
    )
    assert saved.status_code == 200, saved.text
    assert saved.json() == saved_workflow_games(GAMES)

    loaded = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == saved_workflow_games(GAMES)
