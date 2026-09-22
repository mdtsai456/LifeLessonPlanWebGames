"""測試 155：配置頁素材卡與格子改呼叫 materialPreview。"""

from tests.conftest import frontend_js_source, js_function


def test_assign_tiles_call_material_preview(client):
    source = frontend_js_source()
    cards = js_function(source, "memoryLibraryCards")
    market = js_function(source, "marketSlotTile")
    tile = js_function(source, "memorySlotTile")
    for body in (cards, market, tile):
        assert "materialPreview" in body
        assert "materialImg" not in body
