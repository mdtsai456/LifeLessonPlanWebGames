"""測試 31：預設關卡是名稱為預設的故事線。六步的素材 id 都是 null。"""

SIX_STEPS = [
    "MarketShopping",
    "MemoryMatch",
    "PairVacuum",
    "SortArena",
    "DecisionParkour",
    "MarketShoppingBudgetMode",
]


def test_workflow_default_shape(client, auth_headers):
    response = client.get("/api/workflow/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["startNpcName"] == ""
    assert body["startDialogues"] == []
    assert len(body["storylines"]) == 1
    line = body["storylines"][0]
    assert line["name"] == "預設"
    assert line["order"] == 1
    steps = line["steps"]
    assert [item["game"] for item in steps] == SIX_STEPS
    assert [item["order"] for item in steps] == [1, 2, 3, 4, 5, 6]
    for item in steps:
        assert item["gameMaterialCustomizationId"] is None
        assert item["endNpcName"] == ""
        assert item["endDialogues"] == []
