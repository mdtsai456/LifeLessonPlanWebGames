"""測試 84：輸入寫入記憶體。oninput 不重繪整頁。"""

from tests.conftest import frontend_js_source, js_function


def test_app_js_end_dialogue_input_does_not_render(client):
    source = frontend_js_source()
    assert "step.endNpcName = event.target.value" in source
    assert "step.endDialogues[lineIndex] = value" in source
    assert "render()" not in js_function(source, "dialogueControls")
