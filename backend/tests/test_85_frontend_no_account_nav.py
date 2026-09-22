"""測試 85：側欄沒有「帳號」按鈕。"""

from tests.conftest import frontend_js_source, js_function


def test_nav_has_no_account_button(client):
    body = js_function(frontend_js_source(), "renderNav")
    assert 'goTo("account")' not in body
    assert 'text: "帳號"' not in body
    assert 'goTo("home")' in body
