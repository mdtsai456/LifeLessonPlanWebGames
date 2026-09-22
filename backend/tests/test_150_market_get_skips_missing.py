"""測試 150：超市 GET 略過已刪素材。記憶配對缺素材仍回 500。"""

import re

from tests.conftest import (
    make_market_budget_config,
    make_market_shopping_config,
    make_memory_config,
    make_student,
)

MAT_CODE = re.compile(r"MAT[0-9]+", re.IGNORECASE)


def _code_from_item(value: str) -> str:
    match = MAT_CODE.search(value)
    assert match is not None, value
    return match.group(0).upper()


def _slot_for_code(items: dict[str, str], material_code: str) -> str:
    for key, value in items.items():
        if _code_from_item(value) == material_code:
            return key
    raise AssertionError(f"找不到素材 {material_code} 的格子")


def _delete_last_tag_material(client, headers, game_code: str, material_code: str) -> None:
    library = client.get(f"/api/games/{game_code}/library", headers=headers)
    assert library.status_code == 200, library.text
    holders = [
        tag["code"]
        for tag in library.json()
        if any(item["code"] == material_code for item in tag["materials"])
    ]
    assert holders, material_code
    deleted = client.delete(
        f"/api/tags/{holders[-1]}/materials/{material_code}",
        headers=headers,
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["status"] == "deleted"


def test_market_shopping_get_skips_deleted_material(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mkt_skip")
    payload = make_market_shopping_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text

    kept_code, removed_code = payload["basketOrder"]
    kept_slot = _slot_for_code(payload["items"], kept_code)
    removed_slot = _slot_for_code(payload["items"], removed_code)
    _delete_last_tag_material(client, auth_headers, "MarketShopping", removed_code)

    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShopping/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    body = loaded.json()[0]
    assert removed_slot not in body["items"]
    assert kept_slot in body["items"]
    assert removed_code not in body["prices"]
    assert kept_code in body["prices"]
    assert removed_code not in body["basketOrder"]
    assert kept_code in body["basketOrder"]


def test_market_budget_get_skips_deleted_material(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mktb_skip")
    payload = make_market_budget_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text

    kept_code, removed_code = list(payload["prices"])
    kept_slot = _slot_for_code(payload["items"], kept_code)
    removed_slot = _slot_for_code(payload["items"], removed_code)
    _delete_last_tag_material(client, auth_headers, "MarketShopping", removed_code)

    loaded = client.get(
        f"/api/students/{student['id']}/games/MarketShoppingBudgetMode/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    body = loaded.json()[0]
    assert removed_slot not in body["items"]
    assert kept_slot in body["items"]
    assert removed_code not in body["prices"]
    assert kept_code in body["prices"]


def test_memory_get_missing_material_is_still_500(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mem_skip")
    payload = make_memory_config(client, auth_headers)
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text

    removed_code = _code_from_item(payload["items"]["theme_1"])
    _delete_last_tag_material(client, auth_headers, "MemoryMatch", removed_code)

    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 500, loaded.text
    assert loaded.json()["detail"] == "設定檔格式不對"
