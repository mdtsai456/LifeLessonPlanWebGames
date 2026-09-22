"""測試 13：2D 生成的輸入檢查與錯誤碼。"""

from tests.conftest import make_tag


def test_blank_object_name_is_422(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/generate-2d",
        headers=auth_headers,
        json={"objectName": "   "},
    )
    assert response.status_code == 422


def test_unknown_tag_generate_2d_is_404(client, auth_headers):
    response = client.post(
        "/api/tags/NOT_A_TAG/generate-2d",
        headers=auth_headers,
        json={"objectName": "箱子"},
    )
    assert response.status_code == 404


def test_generate_2d_unavailable_is_503(client, auth_headers, monkeypatch):
    from backend.gpu_job import UnavailableError

    tag = make_tag(client, auth_headers)

    def boom(_name, _dest):
        raise UnavailableError("找不到 text2image")

    monkeypatch.setattr("backend.generate.generate_png_to_path", boom)
    response = client.post(
        f"/api/tags/{tag}/generate-2d",
        headers=auth_headers,
        json={"objectName": "箱子"},
    )
    assert response.status_code == 503


def test_generate_2d_failure_is_500(client, auth_headers, monkeypatch):
    tag = make_tag(client, auth_headers)

    def boom(_name, _dest):
        raise RuntimeError("gpu died")

    monkeypatch.setattr("backend.generate.generate_png_to_path", boom)
    response = client.post(
        f"/api/tags/{tag}/generate-2d",
        headers=auth_headers,
        json={"objectName": "箱子"},
    )
    assert response.status_code == 500
