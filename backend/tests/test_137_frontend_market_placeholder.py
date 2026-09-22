"""測試 137：未知遊戲配置頁仍顯示稍後提供。"""

from tests.conftest import frontend_js_source, js_function


def test_unknown_game_assign_stays_placeholder(client):
    source = frontend_js_source()
    page = js_function(source, "assignPage")
    assert "配置功能稍後提供" in page
    assert "vacuumAssignPage(game)" in page
    assert "parkourAssignPage(game)" in page
    assert "sortAssignPage(game)" in page
