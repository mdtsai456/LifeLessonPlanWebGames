"""測試 136：配置頁沒有配置名稱輸入框。"""

from tests.conftest import frontend_js_source


def test_app_js_has_no_assignment_name_input(client):
    source = frontend_js_source()
    assert "memory-name-input" not in source
    assert 'data-field="assignment-name"' not in source
    assert 'placeholder="配置名稱"' not in source
