"""測試 122：切分類重繪後，分類列捲動位置保持不變。"""

from tests.conftest import frontend_js_source, js_function


def test_tab_scroll_position_is_kept(client):
    source = frontend_js_source()
    bind = js_function(source, "bindLibTabScroller")
    scroll = js_function(source, "scrollLibTabs")
    render = js_function(source, "render")
    clear = js_function(source, "clearSession")
    assert "libTabScroll" in bind
    assert "scrollLeft" in bind
    assert "scrollBy" in scroll
    assert "bindLibTabScroller()" in render
    assert "libTabScroll = 0" in clear
