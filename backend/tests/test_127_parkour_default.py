"""測試 127：決策跑酷 Default 可讀。決策跑酷 Default 為 18 格。干擾不來自 TRANSPORT。"""

from tests.conftest import PARKOUR_DISTRACTOR_KEYS, PARKOUR_THEME_KEYS

PARKOUR_THEME_CODES = ("MAT108", "MAT109", "MAT110", "MAT111", "MAT112", "MAT113")


def test_parkour_default_ok(client, auth_headers):
    response = client.get("/api/games/DecisionParkour/materials/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["game"] == "DecisionParkour"
    assert "tag" in body
    assert "items" in body


def test_parkour_default_shape(client, auth_headers):
    body = client.get("/api/games/DecisionParkour/materials/default", headers=auth_headers).json()
    assert body["tag"] == "TRANSPORT"
    assert set(body["items"]) == set(PARKOUR_THEME_KEYS + PARKOUR_DISTRACTOR_KEYS)
    for key, code in zip(PARKOUR_THEME_KEYS, PARKOUR_THEME_CODES, strict=True):
        assert body["items"][key].startswith("/static/")
        assert code in body["items"][key]
    for key in PARKOUR_DISTRACTOR_KEYS:
        assert body["items"][key].startswith("/static/")
        assert "MAT113" not in body["items"][key]
    assert "Start_NPC_Name" in body
    assert isinstance(body["Start_Dialogues"], list)
