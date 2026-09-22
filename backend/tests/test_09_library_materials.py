"""測試 9：新增、改名、換圖、刪素材。修改 GameMaterial 與 GameMaterialTag。"""

from tests.conftest import TEST_TAG_NAME, TINY_PNG, make_tag
from backend.database import connect_db


def test_add_material_without_image(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_椅子"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["code"].startswith("MAT")
    assert body["name"] == "zz_pytest_椅子"
    assert body["image_url"].split("?", 1)[0].endswith(".svg")

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    assert any(item["code"] == body["code"] for item in listed["materials"])

    static = client.get(body["image_url"])
    assert static.status_code == 200
    assert b"<svg" in static.content


def test_add_material_with_png(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_糖"},
        files={"image": ("candy.png", TINY_PNG, "image/png")},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]
    assert created.json()["image_url"].split("?", 1)[0].endswith(".png")
    static = client.get(created.json()["image_url"])
    assert static.status_code == 200
    assert static.content[:8] == b"\x89PNG\r\n\x1a\n"

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    assert any(item["code"] == code for item in listed["materials"])


def test_reject_exe_upload(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_壞檔"},
        files={"image": ("virus.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_blank_material_name_is_400(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "   "},
    )
    assert response.status_code == 400


def test_add_material_on_unknown_tag_is_404(client, auth_headers):
    response = client.post(
        "/api/tags/NOT_A_TAG/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_幽靈"},
    )
    assert response.status_code == 404


def test_rename_and_rename_to_same_name(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_舊名"},
    )
    code = created.json()["code"]

    renamed = client.patch(
        f"/api/materials/{code}",
        headers=auth_headers,
        json={"name": "zz_pytest_新名"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "zz_pytest_新名"

    same = client.patch(
        f"/api/materials/{code}",
        headers=auth_headers,
        json={"name": "zz_pytest_新名"},
    )
    assert same.status_code == 200, same.text
    assert same.json()["name"] == "zz_pytest_新名"

    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    match = next(item for item in listed["materials"] if item["code"] == code)
    assert match["name"] == "zz_pytest_新名"


def test_rename_unknown_material_is_404(client, auth_headers):
    response = client.patch(
        "/api/materials/MAT99999",
        headers=auth_headers,
        json={"name": "zz_pytest_沒這筆"},
    )
    assert response.status_code == 404


def test_replace_image(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_換圖"},
    )
    code = created.json()["code"]
    old_url = created.json()["image_url"]
    assert old_url.split("?", 1)[0].endswith(".svg")

    replaced = client.put(
        f"/api/materials/{code}/image",
        headers=auth_headers,
        files={"image": ("new.png", TINY_PNG, "image/png")},
    )
    assert replaced.status_code == 200, replaced.text
    assert replaced.json()["image_url"].split("?", 1)[0].endswith(".png")
    assert client.get(replaced.json()["image_url"]).status_code == 200
    assert client.get(old_url).status_code == 404


def test_replace_image_unknown_material_is_404(client, auth_headers):
    response = client.put(
        "/api/materials/MAT99999/image",
        headers=auth_headers,
        files={"image": ("new.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 404


def test_delete_material_only_in_one_tag(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_刪掉"},
    )
    code = created.json()["code"]
    image_url = created.json()["image_url"]
    deleted = client.delete(f"/api/tags/{tag}/materials/{code}", headers=auth_headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
    listed = client.get(f"/api/tags/{tag}/materials", headers=auth_headers).json()
    assert all(item["code"] != code for item in listed["materials"])
    assert client.get(image_url).status_code == 404


def test_unlink_when_material_is_on_two_tags(client, auth_headers):
    """同一素材在兩個分類時，從一個分類刪除只解除關聯。檔案仍存在。"""
    first = make_tag(client, auth_headers)
    second = make_tag(client, auth_headers, name=TEST_TAG_NAME + "二")
    created = client.post(
        f"/api/tags/{first}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_共用"},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]
    image_url = created.json()["image_url"]

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM Tag WHERE tag_code = %s", (second,))
            tag_row = cursor.fetchone()
            cursor.execute("SELECT id FROM GameMaterial WHERE material_code = %s", (code,))
            material_row = cursor.fetchone()
            cursor.execute(
                "INSERT INTO GameMaterialTag (game_material_id, tag_id) VALUES (%s, %s)",
                (material_row["id"], tag_row["id"]),
            )
            connection.commit()
    finally:
        connection.close()

    unlinked = client.delete(f"/api/tags/{first}/materials/{code}", headers=auth_headers)
    assert unlinked.status_code == 200
    assert unlinked.json()["status"] == "unlinked"
    left_on_first = client.get(f"/api/tags/{first}/materials", headers=auth_headers).json()
    left_on_second = client.get(f"/api/tags/{second}/materials", headers=auth_headers).json()
    assert all(item["code"] != code for item in left_on_first["materials"])
    assert any(item["code"] == code for item in left_on_second["materials"])
    assert client.get(image_url).status_code == 200


def test_delete_unknown_material_is_404(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.delete(f"/api/tags/{tag}/materials/MAT99999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_material_not_in_this_tag_is_404(client, auth_headers):
    first = make_tag(client, auth_headers)
    second = make_tag(client, auth_headers, name=TEST_TAG_NAME + "二")
    created = client.post(
        f"/api/tags/{first}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_別欄"},
    )
    code = created.json()["code"]
    response = client.delete(f"/api/tags/{second}/materials/{code}", headers=auth_headers)
    assert response.status_code == 404
    still = client.get(f"/api/tags/{first}/materials", headers=auth_headers).json()
    assert any(item["code"] == code for item in still["materials"])
