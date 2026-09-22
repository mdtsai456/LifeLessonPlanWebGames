"""測試 67：Placeholder SVG 會跳脫名稱首字。"""

from tests.conftest import make_tag


def test_placeholder_svg_escapes_lt(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "<zz_pytest_lt"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    try:
        static = client.get(body["image_url"])
        assert static.status_code == 200
        assert ">&lt;</text>" in static.text
        assert "><</text>" not in static.text
    finally:
        client.delete(f"/api/tags/{tag}/materials/{body['code']}", headers=auth_headers)
