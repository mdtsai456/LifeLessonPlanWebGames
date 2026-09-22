"""測試 121：素材庫分類不換行。中間軌道橫向捲動。"""


def test_lib_tabs_do_not_wrap(client):
    css = client.get("/css/styles.css").text
    assert ".tab-scroller {" in css
    assert ".tab-scroller-track {" in css
    assert ".memory-lib-head .tabs" in css
    assert "flex-wrap: nowrap" in css
    assert "overflow-x: auto" in css
    assert ".tab-scroll-btn" in css
