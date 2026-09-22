"""測試 23：前端 app.js 不再出現舊文案 2D cube / 3D model。"""

from tests.conftest import frontend_js_source


def test_app_js_has_no_2d_cube(client):
    source = frontend_js_source()
    assert "2D cube" not in source


def test_app_js_has_no_3d_model(client):
    source = frontend_js_source()
    assert "3D model" not in source
