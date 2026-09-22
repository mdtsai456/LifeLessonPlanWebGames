"""測試 63：側欄沒學生時會提示先新增。"""

from tests.conftest import frontend_js_source


def test_app_js_student_select_empty(client):
    source = frontend_js_source()
    assert "請先新增學生" in source
    assert 'aria-label": "選擇學生"' in source
