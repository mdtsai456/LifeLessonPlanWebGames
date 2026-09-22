"""測試 120：素材庫分類列是單列橫向捲動，左右有箭頭。"""

from tests.conftest import frontend_js_source, js_function


def test_library_has_tab_scroller(client):
    library = js_function(frontend_js_source(), "memoryLibraryPanel")
    assert "tab-scroller" in library
    assert "tab-scroller-track" in library
    assert "tab-scroll-btn" in library
    assert "上一個分類" in library
    assert "下一個分類" in library
    assert "assignLibTag" in library
    assert "setAssignmentTag" not in library
