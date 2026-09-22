"""測試 16：temp_id 不合法或找不到檔時，入庫回 400。"""

from tests.conftest import make_tag


def test_temp_id_with_slash_is_400(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_壞暫存", "temp_id": "abc/def"},
    )
    assert response.status_code == 400


def test_temp_id_with_dot_is_400(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_壞暫存", "temp_id": "abc.def"},
    )
    assert response.status_code == 400


def test_missing_temp_file_is_400(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_過期", "temp_id": "deadbeefdeadbeefdeadbeefdeadbeef"},
    )
    assert response.status_code == 400
