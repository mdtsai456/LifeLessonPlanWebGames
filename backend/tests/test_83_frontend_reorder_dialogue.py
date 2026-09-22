"""測試 83：拖曳改順序時，結束對話留在同一張卡片。"""

from tests.conftest import frontend_js_source


def test_app_js_reorder_keeps_end_dialogue(client):
    source = frontend_js_source()
    assert "const [moved] = next.splice(fromIndex, 1);" in source
    assert "next.splice(toIndex, 0, moved);" in source
