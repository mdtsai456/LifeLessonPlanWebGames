"""測試 26：入庫只傳送名稱。函式本體不含 temp_id。"""

from tests.conftest import frontend_js_source, js_function


def test_add_material_by_name_posts_only_name(client):
    body = js_function(frontend_js_source(), "addMaterialByName")
    assert 'append("name"' in body
    assert "temp_id" not in body
