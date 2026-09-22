"""測試 70：儲存配置會送出結束對話欄位。"""

from tests.conftest import frontend_js_source


def test_app_js_saves_end_dialogues(client):
    source = frontend_js_source()
    assert "endNpcName" in source
    assert "endDialogues" in source
    assert "/api/students/${studentId}/workflow" in source
