"""測試 69：關卡頁有結束對話面板。"""

from tests.conftest import frontend_js_source


def test_app_js_has_end_dialogue_panel(client):
    source = frontend_js_source()
    assert "閉場" in source
    assert "NPC 名字" in source
