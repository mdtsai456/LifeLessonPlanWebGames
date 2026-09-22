"""測試 157：png 換成另一張 png 時，問號前仍是 .png。兩次 ?v= 不同。資料庫 file_path 不含問號。"""

from backend.database import connect_db
from tests.conftest import TINY_PNG, make_tag


def test_replace_png_with_png_changes_version(client, auth_headers):
    tag = make_tag(client, auth_headers)
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_同尾"},
        files={"image": ("first.png", TINY_PNG, "image/png")},
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]
    first_url = created.json()["image_url"]

    replaced = client.put(
        f"/api/materials/{code}/image",
        headers=auth_headers,
        files={"image": ("second.png", TINY_PNG, "image/png")},
    )
    assert replaced.status_code == 200, replaced.text
    second_url = replaced.json()["image_url"]

    assert first_url.split("?", 1)[0].endswith(".png")
    assert second_url.split("?", 1)[0].endswith(".png")
    assert first_url.split("?v=", 1)[1] != second_url.split("?v=", 1)[1]

    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT file_path FROM GameMaterial WHERE material_code = %s",
                (code,),
            )
            row = cursor.fetchone()
    finally:
        connection.close()
    assert "?" not in row["file_path"]
