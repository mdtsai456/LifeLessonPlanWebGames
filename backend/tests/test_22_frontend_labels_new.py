"""測試 22：前端 app.js 已改成 Image / Model 新文案。"""

from tests.conftest import frontend_js_source


def test_app_js_served(client):
    response = client.get("/js/app.js")
    assert response.status_code == 200
    assert "text:" in response.text


def test_type_choice_has_image_button(client):
    source = frontend_js_source()
    assert 'text: "Image"' in source


def test_type_choice_has_model_button(client):
    source = frontend_js_source()
    assert 'text: "Model"' in source


def test_add_form_title_image(client):
    source = frontend_js_source()
    assert "新增 Image" in source


def test_add_form_title_model(client):
    source = frontend_js_source()
    assert "新增 Model" in source
