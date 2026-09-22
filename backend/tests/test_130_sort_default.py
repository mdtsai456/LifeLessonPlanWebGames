"""測試 130：分類推物 Default 可讀，四主題各 5 格且互不重疊。"""

from tests.conftest import SORT_SLOT_KEYS

SORT_DEFAULT_TAGS = ("CLASSROOM_CLEANING", "EDIBLE", "PARK", "TRANSPORT")
SORT_DEFAULT_CODES = {
    "bin_1_1": "MAT069",
    "bin_1_2": "MAT070",
    "bin_1_3": "MAT071",
    "bin_1_4": "MAT072",
    "bin_1_5": "MAT073",
    "bin_2_1": "MAT003",
    "bin_2_2": "MAT004",
    "bin_2_3": "MAT005",
    "bin_2_4": "MAT006",
    "bin_2_5": "MAT007",
    "bin_3_1": "MAT013",
    "bin_3_2": "MAT014",
    "bin_3_3": "MAT057",
    "bin_3_4": "MAT115",
    "bin_3_5": "MAT116",
    "bin_4_1": "MAT108",
    "bin_4_2": "MAT109",
    "bin_4_3": "MAT110",
    "bin_4_4": "MAT111",
    "bin_4_5": "MAT112",
}


def test_sort_default_ok(client, auth_headers):
    response = client.get("/api/games/SortArena/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "SortArena"
    assert "tags" in body
    assert "items" in body


def test_sort_default_shape(client, auth_headers):
    body = client.get("/api/games/SortArena/materials/default", headers=auth_headers).json()
    assert body["tags"] == list(SORT_DEFAULT_TAGS)
    assert set(body["items"]) == set(SORT_SLOT_KEYS)
    for key, code in SORT_DEFAULT_CODES.items():
        assert body["items"][key].startswith("/static/")
        assert code in body["items"][key]
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
