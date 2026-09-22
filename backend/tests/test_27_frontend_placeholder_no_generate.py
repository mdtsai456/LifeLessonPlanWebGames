"""測試 27：此表單不呼叫生成預覽。也不呼叫 generate API。"""

from tests.conftest import frontend_js_source, js_function


def test_placeholder_form_does_not_generate(client):
    body = js_function(frontend_js_source(), "openAddPlaceholderForm")
    assert "生成預覽" not in body
    assert "generate-2d" not in body
    assert "generate-3d" not in body
