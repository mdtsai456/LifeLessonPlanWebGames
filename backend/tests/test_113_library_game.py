"""測試 113：配置頁一次載入該遊戲全部分類與素材。"""

from tests.conftest import make_tag


def test_memory_library_lists_pytest_tag(client, auth_headers):
    tag = make_tag(client, auth_headers, game_code="MemoryMatch", name="zz_pytest_配置庫")
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": "zz_pytest_配置卡"},
    )
    assert created.status_code == 201, created.text
    response = client.get("/api/games/MemoryMatch/library", headers=auth_headers)
    assert response.status_code == 200, response.text
    rows = response.json()
    found = next(row for row in rows if row["code"] == tag)
    assert found["name"] == "zz_pytest_配置庫"
    assert any(item["code"] == created.json()["code"] for item in found["materials"])
