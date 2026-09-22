"""測試 123：配對吸塵 Default 可讀，且為 5 格同一主題。"""

from tests.conftest import VACUUM_SLOT_KEYS

VACUUM_DEFAULT_CODES = ("MAT069", "MAT070", "MAT071", "MAT072", "MAT073")


def test_vacuum_default_ok(client, auth_headers):
    response = client.get("/api/games/PairVacuum/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "PairVacuum"
    assert "tag" in body
    assert "items" in body


def test_vacuum_default_shape(client, auth_headers):
    body = client.get("/api/games/PairVacuum/materials/default", headers=auth_headers).json()
    assert body["tag"] == "CLASSROOM_CLEANING"
    assert set(body["items"]) == set(VACUUM_SLOT_KEYS)
    for key, code in zip(VACUUM_SLOT_KEYS, VACUUM_DEFAULT_CODES, strict=True):
        assert body["items"][key].startswith("/static/")
        assert code in body["items"][key]
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
