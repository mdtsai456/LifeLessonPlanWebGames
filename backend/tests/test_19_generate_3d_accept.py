"""測試 19：3D 暫存 GLB 加入素材庫。卡片使用 model_url。"""

from tests.conftest import TINY_PNG, make_tag
from backend.database import STATIC_DIR


def test_accept_3d_temp_moves_into_library(client, auth_headers):
    tag = make_tag(client, auth_headers)
    preview = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert preview.status_code == 200, preview.text
    temp_id = preview.json()["tempId"]
    tmp_url = preview.json()["modelUrl"]

    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_紅椅", "temp_id": temp_id},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "zz_pytest_紅椅"
    assert body["model_url"].startswith("/static/GameMaterial/Shared/")
    assert body["model_url"].split("?", 1)[0].endswith(".glb")
    assert "image_url" not in body
    assert "/tmp/" not in body["model_url"]

    static = client.get(body["model_url"])
    assert static.status_code == 200
    assert client.get(tmp_url).status_code == 404
    assert not (STATIC_DIR / "GameMaterial" / "tmp" / f"{temp_id}.glb").exists()

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    match = next(item for item in listed["materials"] if item["code"] == body["code"])
    assert match["model_url"] == body["model_url"]


def test_3d_material_cannot_replace_image(client, auth_headers):
    tag = make_tag(client, auth_headers)
    preview = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_紅椅", "temp_id": preview.json()["tempId"]},
    )
    assert created.status_code == 201, created.text
    response = client.put(
        f"/api/materials/{created.json()['code']}/image",
        headers=auth_headers,
        files={"image": ("new.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 400
