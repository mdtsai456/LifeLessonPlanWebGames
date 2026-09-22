"""測試 92：首頁顯示老師問候。未知 hash 也顯示此頁。"""

from tests.conftest import frontend_js_source, js_function


def test_home_page_greets_teacher(client):
    body = js_function(frontend_js_source(), "homePage")
    assert 'text: "首頁"' in body
    assert "你好，${name}" in body


def test_render_content_falls_back_to_home(client):
    body = js_function(frontend_js_source(), "renderContent")
    assert "homePage()" in body
    assert 'page === "materials"' in body
    assert 'page === "students"' in body
    assert 'page === "workflow"' in body
