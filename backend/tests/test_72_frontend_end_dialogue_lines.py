"""測試 72：結束對話可新增與刪除對白。"""

from tests.conftest import frontend_js_source


def test_app_js_can_edit_end_dialogue_lines(client):
    source = frontend_js_source()
    assert "新增對白" in source
    assert "deleteEndDialogueLine" in source
    assert "endDialogues.push" in source
