"""測試 24：選擇畫面出現 Placeholder 按鈕。"""

from tests.conftest import frontend_js_source


def test_type_choice_has_placeholder_button(client):
    source = frontend_js_source()
    assert 'text: "Placeholder"' in source
