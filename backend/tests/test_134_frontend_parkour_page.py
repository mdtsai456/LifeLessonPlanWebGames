"""測試 134：決策跑酷配置頁是寬版，有題目主題與 6 列。"""

from tests.conftest import frontend_js_source, js_function


def test_parkour_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "parkourAssignPage")
    shell = js_function(source, "assignShell")
    place = js_function(source, "placeThemeSlots")
    place_parkour = js_function(source, "placeParkour")
    picker = js_function(source, "parkourThemePicker")
    set_tag = js_function(source, "setParkourTag")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "在六段路途中選對正確的那一條" in page
    assert "is-wide" in page
    assert "題目主題" in picker
    assert "memory-theme-pick" in picker
    assert "parkour-rows" in page
    assert "第 ${index} 列" in page
    assert "theme_${index}" in page
    assert "distractor_${2 * index - 1}" in page
    assert "startNpcPanel()" in shell
    assert "memoryLibraryPanel()" in shell
    assert "memory-name-input" not in page
    assert "請先選擇題目主題" in place_parkour
    assert "這個素材已經在其他格子" in place
    assert "applyThemeTag" in set_tag
    assert "syncAssignDom" in set_tag
    assert ".memory-theme-pick" in css
    assert ".slot-grid.parkour-rows" in css
    parkour_rule = css.split(".slot-grid.parkour-rows", 1)[1].split("}", 1)[0]
    assert "repeat(auto-fill, minmax(7.2rem, 1fr))" in parkour_rule
    assert ".market-shelf-scroll" in css
    assert ".market-shelf-group" in css


def test_assign_page_parkour_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "DECISION_PARKOUR" in body
    assert "parkourAssignPage(game)" in body
