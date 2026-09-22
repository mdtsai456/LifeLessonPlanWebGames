"""測試 55：側欄可進入學生頁。並呼叫學生 API。"""

from tests.conftest import frontend_js_source


def test_app_js_has_students_route(client):
    source = frontend_js_source()
    assert 'goTo("students")' in source


def test_app_js_has_add_student(client):
    source = frontend_js_source()
    assert "新增學生" in source
    assert "/api/students" in source
