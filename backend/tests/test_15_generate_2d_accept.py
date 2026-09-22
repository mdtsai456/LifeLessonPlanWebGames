"""測試 15：2D 暫存 PNG 加入素材庫。移到 Shared。"""

from tests.conftest import make_tag
from backend.database import STATIC_DIR


def test_accept_2d_temp_moves_into_library(client, auth_headers):
    tag = make_tag(client, auth_headers)
    preview = client.post(
        f"/api/tags/{tag}/generate-2d",
        headers=auth_headers,
        json={"objectName": "zz_pytest_木箱"},
    )
    assert preview.status_code == 200, preview.text
    temp_id = preview.json()["tempId"]
    tmp_url = preview.json()["imageUrl"]

    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_木箱", "temp_id": temp_id},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "zz_pytest_木箱"
    assert body["image_url"].startswith("/static/GameMaterial/Shared/")
    assert body["image_url"].split("?", 1)[0].endswith(".png")
    assert "/tmp/" not in body["image_url"]

    static = client.get(body["image_url"])
    assert static.status_code == 200
    assert static.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert client.get(tmp_url).status_code == 404
    assert not (STATIC_DIR / "GameMaterial" / "tmp" / f"{temp_id}.png").exists()

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    assert any(item["code"] == body["code"] for item in listed["materials"])
