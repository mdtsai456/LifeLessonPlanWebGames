"""測試 88：未知 hash 當首頁。舊 #account 不是獨立頁。"""

from tests.conftest import frontend_js_source, js_function


def test_parse_route_unknown_is_home(client):
    body = js_function(frontend_js_source(), "parseRoute")
    assert "SIMPLE_PAGES.has(raw)" in body
    assert 'page: "home"' in body
    assert "account" not in body


def test_render_content_has_no_account_branch(client):
    body = js_function(frontend_js_source(), "renderContent")
    assert 'page === "account"' not in body
    assert "accountPage()" not in body
    assert "homePage()" in body
