"""測試 154：故事線有指定 id 的步驟用該筆，null 用 Default。整包沒有頂層 games。"""

from backend.material import SUPPORTED_GAMES
from tests.conftest import (
    UNITY_TEST_KEY,
    make_memory_config,
    make_student,
    make_vacuum_config,
    saved_workflow_games,
)

CUSTOM_GAMES = ("MemoryMatch", "PairVacuum")


def test_unity_pack_uses_partial_custom(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_mix")
    memory = make_memory_config(client, auth_headers, npc_name="店員", dialogues=["開始配"])
    vacuum = make_vacuum_config(client, auth_headers, npc_name="清潔員", dialogues=["開始吸"])
    saved_memory = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=memory,
    )
    assert saved_memory.status_code == 201, saved_memory.text
    saved_vacuum = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=vacuum,
    )
    assert saved_vacuum.status_code == 201, saved_vacuum.text

    steps = []
    for order, game_code in enumerate(
        (
            "MarketShopping",
            "MemoryMatch",
            "PairVacuum",
            "SortArena",
            "DecisionParkour",
            "MarketShoppingBudgetMode",
        ),
        start=1,
    ):
        material_id = None
        if game_code == "MemoryMatch":
            material_id = saved_memory.json()["id"]
        if game_code == "PairVacuum":
            material_id = saved_vacuum.json()["id"]
        steps.append(
            {
                "game": game_code,
                "order": order,
                "gameMaterialCustomizationId": material_id,
            }
        )
    saved_workflow = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=saved_workflow_games(steps),
    )
    assert saved_workflow.status_code == 200, saved_workflow.text

    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    response = client.get(f"/api/unity/students/{student['id']}", headers=unity_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["studentName"] == student["username"]
    assert "games" not in body
    packed = {item["game"]: item for item in body["workflow"]["storylines"][0]["steps"]}
    memory_play = client.get(
        f"/api/unity/students/{student['id']}/material-configs/{saved_memory.json()['id']}",
        headers=unity_headers,
    )
    vacuum_play = client.get(
        f"/api/unity/students/{student['id']}/material-configs/{saved_vacuum.json()['id']}",
        headers=unity_headers,
    )
    assert memory_play.status_code == 200, memory_play.text
    assert vacuum_play.status_code == 200, vacuum_play.text
    assert packed["MemoryMatch"]["material"] == memory_play.json()
    assert packed["PairVacuum"]["material"] == vacuum_play.json()
    assert packed["MemoryMatch"]["material"]["Start_NPC_Name"] == "店員"
    assert packed["PairVacuum"]["material"]["Start_NPC_Name"] == "清潔員"
    for game_code in SUPPORTED_GAMES - set(CUSTOM_GAMES):
        single = client.get(
            f"/api/unity/students/{student['id']}/games/{game_code}",
            headers=unity_headers,
        )
        assert single.status_code == 200, single.text
        assert packed[game_code]["gameMaterialCustomizationId"] is None
        assert packed[game_code]["material"] == single.json()
