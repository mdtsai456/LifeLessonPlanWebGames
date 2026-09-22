"""測試 14：MOCK 時 2D 生成會寫入暫存 PNG。"""

from tests.conftest import make_tag


def test_generate_2d_mock_writes_tmp_png(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/generate-2d",
        headers=auth_headers,
        json={"objectName": "zz_pytest_木箱"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tempId"]
    assert body["imageUrl"] == f"/static/GameMaterial/tmp/{body['tempId']}.png"

    static = client.get(body["imageUrl"])
    assert static.status_code == 200
    assert static.content[:8] == b"\x89PNG\r\n\x1a\n"
