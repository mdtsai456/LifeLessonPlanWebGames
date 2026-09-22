"""測試 28：呼叫 API。確認寫出的 SVG 字是名稱首字。"""

from tests.conftest import make_tag


def test_placeholder_svg_uses_first_character(client, auth_headers):
    tag = make_tag(client, auth_headers)
    name = "zz_pytest_木箱"
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": name},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["image_url"].split("?", 1)[0].endswith(".svg")
    assert "model_url" not in body

    static = client.get(body["image_url"])
    assert static.status_code == 200
    label = name.strip()[:1]
    assert f">{label}</text>" in static.text
