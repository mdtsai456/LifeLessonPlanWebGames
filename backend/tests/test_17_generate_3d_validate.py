"""測試 17：3D 生成的輸入檢查與錯誤碼。"""

from pathlib import Path

import pytest

from backend.gpu_job import UnavailableError
from backend.trellis_generate import generate_glb_to_path
from tests.conftest import make_tag


def test_blank_prompt_is_422(client, auth_headers):
    tag = make_tag(client, auth_headers)
    response = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "   "},
    )
    assert response.status_code == 422


def test_unknown_tag_generate_3d_is_404(client, auth_headers):
    response = client.post(
        "/api/tags/NOT_A_TAG/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert response.status_code == 404


def test_generate_3d_unavailable_is_503(client, auth_headers, monkeypatch):
    tag = make_tag(client, auth_headers)

    def boom(_prompt, _dest):
        raise UnavailableError("找不到 Trellis")

    monkeypatch.setattr("backend.generate.generate_glb_to_path", boom)
    response = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert response.status_code == 503


def test_generate_3d_failure_is_500(client, auth_headers, monkeypatch):
    tag = make_tag(client, auth_headers)

    def boom(_prompt, _dest):
        raise RuntimeError("gpu died")

    monkeypatch.setattr("backend.generate.generate_glb_to_path", boom)
    response = client.post(
        f"/api/tags/{tag}/generate-3d",
        headers=auth_headers,
        json={"prompt": "a red chair"},
    )
    assert response.status_code == 500


def test_missing_trellis_python_is_unavailable(monkeypatch, tmp_path: Path):
    """未開啟 MOCK 時必須使用 Trellis 的 Python。不可使用後端 .venv。後端 .venv 沒有 torch。"""
    monkeypatch.setenv("TRELLIS_MOCK", "0")
    monkeypatch.setenv("TRELLIS_PYTHON", str(tmp_path / "nope.exe"))
    with pytest.raises(UnavailableError, match="找不到 Trellis Python"):
        generate_glb_to_path("a red chair", tmp_path / "out.glb")
