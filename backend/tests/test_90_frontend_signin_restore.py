"""測試 90：登入後打開 sessionStorage 裡的目標頁。沒有目標頁時開首頁。"""

from tests.conftest import frontend_js_source, js_function


def test_signin_restores_intended_or_home(client):
    body = js_function(frontend_js_source(), "signIn")
    assert "getItem(INTENDED_KEY)" in body
    assert '|| "home"' in body
    assert "removeItem(INTENDED_KEY)" in body
    assert "location.hash = intended" in body
    assert "account" not in body
