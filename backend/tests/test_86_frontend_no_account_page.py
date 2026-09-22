"""測試 86：沒有帳號測試頁。沒有導向說明文字。"""

import pytest

from tests.conftest import frontend_js_source, js_function


def test_app_js_has_no_account_page(client):
    source = frontend_js_source()
    assert "function accountPage" not in source
    assert "沒登入時打開 #account" not in source
    with pytest.raises(AssertionError, match="找不到 function accountPage"):
        js_function(source, "accountPage")
