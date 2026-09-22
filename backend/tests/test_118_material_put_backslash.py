"""測試 118：PUT 反斜線路徑。GET 回正斜線 /static/，不含 IP。"""

from tests.conftest import make_memory_config, make_student


def test_put_backslash_path_get_forward_slash(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_mat_slash")
    payload = make_memory_config(client, auth_headers)
    payload["items"]["theme_1"] = payload["items"]["theme_1"].replace("/", "\\")
    saved = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert saved.status_code == 201, saved.text
    value = saved.json()["items"]["theme_1"]
    assert value.startswith("/static/")
    assert "\\" not in value
    assert "://" not in value
    loaded = client.get(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()[0]["items"]["theme_1"] == value
