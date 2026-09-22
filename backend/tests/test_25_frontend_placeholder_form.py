"""測試 25：表單標題。輸入時更新色塊預覽。"""

from tests.conftest import frontend_js_source, js_function


def test_add_form_title_placeholder(client):
    source = frontend_js_source()
    assert "新增 Placeholder" in source


def test_placeholder_form_live_preview(client):
    body = js_function(frontend_js_source(), "openAddPlaceholderForm")
    assert "placeholderImage" in body
    assert 'addEventListener("input"' in body
    assert "saveBtn.disabled" in body
