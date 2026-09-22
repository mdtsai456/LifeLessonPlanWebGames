"""測試 64：刪除學生呼叫 DELETE /api/students/{id}。"""

from tests.conftest import frontend_js_source


def test_app_js_deletes_student(client):
    source = frontend_js_source()
    assert 'method: "DELETE"' in source
    assert "/api/students/${id}" in source
