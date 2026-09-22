"""測試 114：記憶配對配置頁有格子、開場 NPC、素材庫。其他遊戲仍佔位。"""

from tests.conftest import frontend_js_source, js_function


def test_memory_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "memoryAssignPage")
    shell = js_function(source, "assignShell")
    npc = js_function(source, "startNpcPanel")
    library = js_function(source, "memoryLibraryPanel")
    place = js_function(source, "placeThemeSlots")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "正確格子" in page
    assert "錯誤格子" in page
    assert "素材庫" in library
    assert "Start_NPC_Name" in npc
    assert "新增對白" in npc
    assert "memory-preview" in shell
    assert "images/memory-board.png" in source
    assert "images/memory-npc.png" in source
    assert "題目主題" not in page
    assert "memory-theme-pick" not in page
    assert "setAssignmentTag" not in library
    assert "materialTagCode" in place
    assert "grid-column: 1 / -1" not in css
    assert "minmax(0, 1fr) minmax(0, 1fr)" in css


def test_memory_preview_images(client):
    board = client.get("/images/memory-board.png")
    npc = client.get("/images/memory-npc.png")
    assert board.status_code == 200
    assert npc.status_code == 200


def test_assign_page_memory_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "MEMORY_MATCH" in body
    assert "memoryAssignPage(game)" in body
    assert "配置功能稍後提供" in body
    assert "請先新增並選擇學生。" in body
