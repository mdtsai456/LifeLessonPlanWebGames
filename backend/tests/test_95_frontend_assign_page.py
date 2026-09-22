"""測試 95：遊戲配置頁依有無學生顯示提示。其他遊戲仍是稍後提供。"""

from tests.conftest import frontend_js_source, js_function


def test_assign_page_shows_student_or_later_hint(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert 'pageHeader("遊戲配置"' in body
    assert "請先新增並選擇學生。" in body
    assert "配置功能稍後提供" in body
    assert "view.studentId" in body


def test_render_content_has_assign_branch(client):
    body = js_function(frontend_js_source(), "renderContent")
    assert 'page === "assign"' in body
    assert "assignPage()" in body


def test_handle_route_resolves_assign_game(client):
    body = js_function(frontend_js_source(), "handleRoute")
    assert 'page === "assign"' in body
    assert "assign/${nextGame}" in body
    assert 'route.page === "students" || route.page === "workflow" || route.page === "assign"' in body
