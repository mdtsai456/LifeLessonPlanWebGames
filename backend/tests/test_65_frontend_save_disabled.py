"""測試 65：沒選學生時，儲存配置按鈕是 disabled。"""

from tests.conftest import frontend_js_source


def test_app_js_save_disabled_without_student(client):
    source = frontend_js_source()
    assert "disabled: !view.studentId" in source
