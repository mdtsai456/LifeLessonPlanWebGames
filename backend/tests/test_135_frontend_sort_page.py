"""測試 135：分類推物配置頁是寬版，可選 4 主題，改選會 remapFilled。"""

from tests.conftest import frontend_js_source, js_function


def test_sort_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "sortAssignPage")
    shell = js_function(source, "assignShell")
    place = js_function(source, "placeSort")
    picker = js_function(source, "sortThemePicker")
    toggle = js_function(source, "toggleSortTag")
    remap = js_function(source, "remapFilled")
    save = js_function(source, "saveAssignment")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "把物品推到對應的四個分類" in page
    assert "先選四個分類主題，每個分類拖五個素材。學生須把物品推到正確的分類。" in page
    assert "sort-slots" in page
    assert "is-wide" in page
    assert "分類主題" in picker
    assert "memory-theme-pick" in picker
    assert "market-shelf-scroll" in page
    assert "bin_${bin}_" in page
    assert "startNpcPanel()" in shell
    assert "memoryLibraryPanel()" in shell
    assert "memory-name-input" not in page
    assert "請先選滿 4 個分類主題" in place
    assert "這個素材已經在其他格子" in place
    assert "remapFilled" in toggle
    assert "bin_" in remap
    assert "assignment.tags" in save
    assert "SORT_ARENA" in save
    assert 'payloadBody.tag = assignment.tag' in save or "payloadBody.tag =" in save
    assert ".market-shelf-group" in css
    assert ".slot-grid.sort-slots" in css
    sort_rule = css.split(".slot-grid.sort-slots", 1)[1].split("}", 1)[0]
    assert "repeat(5, minmax(0, 1fr))" in sort_rule
    assert ".slot-grid.sort-slots" in css.split("@media (max-width: 900px)", 1)[1]


def test_assign_page_sort_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "SORT_ARENA" in body
    assert "sortAssignPage(game)" in body
