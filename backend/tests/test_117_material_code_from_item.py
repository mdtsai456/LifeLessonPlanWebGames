"""測試 117：格子值可以是代碼或路徑。一律取出 MAT 代碼。"""

import pytest
from fastapi import HTTPException

from backend.material import material_code_from_item


def test_plain_code():
    assert material_code_from_item("MAT003") == "MAT003"


def test_static_svg_path():
    assert material_code_from_item("/static/GameMaterial/Shared/MAT003.svg") == "MAT003"


def test_backslash_png_path():
    assert material_code_from_item("\\static\\GameMaterial\\Shared\\MAT187.png") == "MAT187"


def test_lowercase_code():
    assert material_code_from_item("mat012") == "MAT012"


def test_empty_is_400():
    with pytest.raises(HTTPException) as caught:
        material_code_from_item("   ")
    assert caught.value.status_code == 400
    assert caught.value.detail == "找不到素材代碼"


def test_text_without_code_is_400():
    with pytest.raises(HTTPException) as caught:
        material_code_from_item("/static/nope.png")
    assert caught.value.status_code == 400
