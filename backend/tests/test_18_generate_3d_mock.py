"""測試 18：MOCK 時 3D 生成會寫入暫存 GLB。"""

from tests.conftest import make_tag


def test_generate_3d_mock_writes_tmp_glb(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tempId"]
    assert body["modelUrl"] == f"/static/GameMaterial/tmp/{body['tempId']}.glb"

    static = client.get(body["modelUrl"])
    assert static.status_code == 200
    assert static.content.startswith(b"glTF")


def test_generate_3d_appends_style_suffix(client, auth_headers, monkeypatch):
    seen = {}

    def fake(prompt, dest):
        seen["prompt"] = prompt
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"glTF-MOCK")

    monkeypatch.setattr("backend.generate.generate_glb_to_path", fake)
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert response.status_code == 200, response.text
    assert seen["prompt"] == "a red chair (low poly, with smooth curve)"
