"""測試 89：未登入只記住已知目標頁。首頁與未知路徑不寫入。"""

from tests.conftest import frontend_js_source, js_function


def test_remember_intended_skips_home_and_unknown(client):
    body = js_function(frontend_js_source(), "rememberIntended")
    assert 'raw === "home"' in body
    assert "SIMPLE_PAGES.has(raw)" in body
    assert 'raw === "materials"' in body
    assert 'raw.startsWith("materials/")' in body
    assert "setItem(INTENDED_KEY" in body
    assert "account" not in body
