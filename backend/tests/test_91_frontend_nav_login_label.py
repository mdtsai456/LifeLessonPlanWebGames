"""測試 91：側欄仍有首頁、學生、關卡配置、登出。登入表單仍有帳號欄。"""

from tests.conftest import frontend_js_source, js_function


def test_nav_keeps_real_pages(client):
    body = js_function(frontend_js_source(), "renderNav")
    assert 'text: "首頁"' in body
    assert 'goTo("students")' in body
    assert 'text: "關卡配置"' in body
    assert 'goTo("workflow")' in body
    assert "登出" in body


def test_login_form_still_has_username_field(client):
    body = js_function(frontend_js_source(), "loginPage")
    assert '"aria-label": "帳號"' in body
    assert "帳號" in body
    assert "signIn()" in body
