"""測試 94：#assign/<game> 是遊戲配置頁。未登入也會記住這條路徑。"""

from tests.conftest import frontend_js_source, js_function


def test_parse_route_reads_assign_game(client):
    body = js_function(frontend_js_source(), "parseRoute")
    assert 'raw === "assign"' in body
    assert 'raw.startsWith("assign/")' in body
    assert 'page: "assign"' in body


def test_remember_intended_keeps_assign(client):
    body = js_function(frontend_js_source(), "rememberIntended")
    assert 'raw === "assign"' in body
    assert 'raw.startsWith("assign/")' in body
