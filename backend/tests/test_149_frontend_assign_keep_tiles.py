"""測試 149：配置頁同步時，沒變的格子、對白、素材卡不刪除後重建。"""

from tests.conftest import frontend_js_source, js_function


def test_fill_slot_skips_unchanged_item(client):
    fill = js_function(frontend_js_source(), "fillSlotTile")
    tile = js_function(frontend_js_source(), "memorySlotTile")
    market = js_function(frontend_js_source(), "marketSlotTile")
    assert "data-item" in fill
    assert 'getAttribute("data-item")' in fill
    assert "replaceChildren" in fill
    assert '"data-item"' in tile
    assert '"data-item"' in market


def test_npc_lines_keep_rows_when_count_matches(client):
    body = js_function(frontend_js_source(), "refreshNpcLines")
    assert "children.length" in body
    assert "replaceChildren" in body


def test_library_cards_reused_per_tag(client):
    cards = js_function(frontend_js_source(), "memoryLibraryCards")
    load = js_function(frontend_js_source(), "loadAssignLibrary")
    assert ".get(" in cards
    assert ".set(" in cards
    assert ".clear(" in load
