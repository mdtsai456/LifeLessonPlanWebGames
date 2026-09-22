"""測試 10：006 不同老師看到同一份該遊戲素材庫。"""

from tests.conftest import TEST_TAG_NAME, make_tag


def test_other_teacher_sees_new_tag(client, auth_headers, other_auth_headers):
    created = client.post(
        "/api/games/MarketShopping/tags",
        headers=auth_headers,
        json={"name": TEST_TAG_NAME},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]

    tags = client.get("/api/games/MarketShopping/tags", headers=other_auth_headers).json()
    assert any(row["code"] == code and row["name"] == TEST_TAG_NAME for row in tags)


def test_other_teacher_sees_new_material(client, auth_headers, other_auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_共享椅"},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]

    listed = client.get(f"/api/tags/{tag}/materials", headers=other_auth_headers).json()
    assert any(item["code"] == code and item["name"] == "zz_pytest_共享椅" for item in listed["materials"])


def test_other_teacher_can_rename_shared_material(client, auth_headers, other_auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_原名"},
    )
    code = created.json()["code"]

    renamed = client.patch(
        f"/api/materials/{code}",
        headers=other_auth_headers,
        json={"name": "zz_pytest_他改的"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "zz_pytest_他改的"

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    match = next(item for item in listed["materials"] if item["code"] == code)
    assert match["name"] == "zz_pytest_他改的"
