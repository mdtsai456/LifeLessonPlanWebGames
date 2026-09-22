"""測試 116：PUT 素材代碼，GET 回不含 IP 的 /static/ 路徑。"""

import re

from tests.conftest import make_memory_config, make_student

MAT_CODE = re.compile(r"MAT[0-9]+", re.IGNORECASE)


def _codes_from_items(items: dict[str, str]) -> dict[str, str]:
    codes = {}
    for key, value in items.items():
        match = MAT_CODE.search(value)
        assert match is not None, value
        codes[key] = match.group(0)
    return codes


def test_put_codes_get_static_paths(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_path")
    payload = make_memory_config(client, auth_headers)
    code_items = _codes_from_items(payload["items"])
    payload["items"] = code_items
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    items = saved.json()["items"]
    for key, code in code_items.items():
        assert items[key].startswith("/static/")
        assert "://" not in items[key]
        assert code in items[key]
    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()[0]["items"] == items
