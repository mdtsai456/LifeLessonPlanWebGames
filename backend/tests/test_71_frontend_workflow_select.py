"""測試 71：點輸送帶卡片可選取該關。"""

from tests.conftest import frontend_js_source


def test_app_js_selects_workflow_step(client):
    source = frontend_js_source()
    assert "workflowIndex" in source
    assert "is-selected" in source
