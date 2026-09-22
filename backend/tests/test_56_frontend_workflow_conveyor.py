"""測試 56：關卡配置頁有輸送帶。卡片可拖曳。"""

from tests.conftest import frontend_js_source


def test_app_js_has_workflow_route(client):
    source = frontend_js_source()
    assert 'goTo("workflow")' in source
    assert "關卡配置" in source


def test_app_js_has_conveyor_drag(client):
    source = frontend_js_source()
    assert "conveyor" in source
    assert 'draggable: "true"' in source
