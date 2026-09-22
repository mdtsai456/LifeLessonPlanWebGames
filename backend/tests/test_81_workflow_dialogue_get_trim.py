"""測試 81：去掉空白後，GET 讀回清理過的對話。"""

from tests.conftest import make_student, storyline_steps, workflow_body

GAMES = [
    {"game": "MarketShopping", "order": 1},
    {
        "game": "MemoryMatch",
        "order": 2,
        "endNpcName": "  阿姨  ",
        "endDialogues": ["  你好  ", "", "下一句"],
    },
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
    {"game": "MarketShoppingBudgetMode", "order": 6, "endNpcName": "", "endDialogues": []},
]


def test_student_workflow_get_returns_trimmed_dialogue(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_gettrim")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert saved.status_code == 200, saved.text

    loaded = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    memory = next(item for item in storyline_steps(loaded.json()) if item["game"] == "MemoryMatch")
    assert memory["endNpcName"] == "阿姨"
    assert memory["endDialogues"] == ["你好", "下一句"]
