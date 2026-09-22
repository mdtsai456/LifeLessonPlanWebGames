"""測試 138：主題列〈〉不冒泡。預覽模式沒變時不重繪。"""

from tests.conftest import frontend_js_source, js_function


def test_theme_pick_scroll_does_not_rerender(client):
    source = frontend_js_source()
    preview = js_function(source, "setMemoryPreview")
    scroller = js_function(source, "themePickScroller")
    scroll = js_function(source, "scrollThemePickTabs")
    assert "memoryPreview === mode" in preview
    assert "stopPropagation" in scroller
    assert ".memory-theme-pick .tab-scroller-track" in scroll
    assert "scrollBy" in scroll
