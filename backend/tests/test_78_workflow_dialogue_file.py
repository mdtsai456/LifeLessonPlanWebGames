"""測試 78：自訂 workflow.json 含結束對話欄位。"""

import json

from tests.conftest import STORAGE_DIR, make_student, workflow_body

GAMES = [
    {"game": "MarketShopping", "order": 1},
    {
        "game": "MemoryMatch",
        "order": 2,
        "endNpcName": "阿姨",
        "endDialogues": ["這一關完成了,我們回家吧!"],
    },
    {"game": "PairVacuum", "order": 3},
    {"game": "SortArena", "order": 4},
    {"game": "DecisionParkour", "order": 5},
    {"game": "MarketShoppingBudgetMode", "order": 6, "endNpcName": "", "endDialogues": []},
]


def test_student_workflow_file_contains_dialogues(
    client, auth_headers, test_teacher
):
    student = make_student(client, auth_headers, "zz_pytest_student_dlg_file")
    saved = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=workflow_body(GAMES),
    )
    assert saved.status_code == 200, saved.text

    path = (
        STORAGE_DIR
        / "GameWorkflowCustomization"
        / test_teacher["username"]
        / student["username"]
        / "workflow.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    memory = next(
        item
        for item in payload["storylines"][0]["steps"]
        if item["game"] == "MemoryMatch"
    )
    assert set(memory.keys()) == {
        "game",
        "gameMaterialCustomizationId",
        "order",
        "endNpcName",
        "endDialogues",
    }
    assert memory["endNpcName"] == "阿姨"
    assert memory["endDialogues"] == ["這一關完成了,我們回家吧!"]
