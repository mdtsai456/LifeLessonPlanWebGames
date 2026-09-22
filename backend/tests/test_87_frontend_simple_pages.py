"""測試 87：簡單頁面只有首頁、學生、關卡。不含 account。"""

from tests.conftest import frontend_js_source


def test_simple_pages_omit_account(client):
    source = frontend_js_source()
    assert 'SIMPLE_PAGES = new Set(["home", "students", "workflow"])' in source
    start = source.index("SIMPLE_PAGES = new Set(")
    end = source.index(");", start)
    assert '"account"' not in source[start:end]
