"""測試 57：儲存配置呼叫學生 workflow PUT。"""

from tests.conftest import frontend_js_source


def test_app_js_saves_student_workflow(client):
    source = frontend_js_source()
    assert "儲存配置" in source
    assert "/api/students/${studentId}/workflow" in source
    assert 'method: "PUT"' in source
