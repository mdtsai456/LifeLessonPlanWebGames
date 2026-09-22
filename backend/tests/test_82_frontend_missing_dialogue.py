"""測試 82：API 缺結束對話欄位時，前端當空白。"""

from tests.conftest import frontend_js_source


def test_app_js_treats_missing_dialogue_as_empty(client):
    source = frontend_js_source()
    assert 'typeof item.endNpcName === "string"' in source
    assert "dialogueLines(item.endDialogues)" in source
    assert 'return lines.length > 0 ? lines : [""];' in source
