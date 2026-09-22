"""測試 133：配對吸塵配置頁有 5 格、開場 NPC、素材庫。第一格決定主題。"""

from tests.conftest import frontend_js_source, js_function


def test_vacuum_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "vacuumAssignPage")
    shell = js_function(source, "assignShell")
    place = js_function(source, "placeThemeSlots")
    npc = js_function(source, "startNpcPanel")
    library = js_function(source, "memoryLibraryPanel")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "用吸塵器吸起五個同一類的物品" in page
    assert "把五個同一分類的物品拖進格子。第一個拖入的物品決定分類。學生必須吸起這五個物品。" in page
    assert "吸塵格子" in page
    assert "VACUUM_SLOTS" in page
    assert "memory-preview" in shell
    assert "startNpcPanel()" in shell
    assert "memoryLibraryPanel()" in shell
    assert "is-wide" not in page
    assert "題目主題" not in page
    assert "memory-name-input" not in page
    assert "slot_1" in source
    assert "slot_5" in source
    assert "素材庫" in library
    assert "Start_NPC_Name" in npc
    assert "materialTagCode" in place
    assert "這個素材已經在其他格子" in place
    assert "images/memory-board.png" in source
    assert "images/memory-npc.png" in source
    assert ".slot-grid.vacuum-slots" in css


def test_assign_page_vacuum_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "PAIR_VACUUM" in body
    assert "vacuumAssignPage(game)" in body


def test_load_assign_library_uses_game_code(client):
    source = frontend_js_source()
    load_lib = js_function(source, "loadAssignLibrary")
    load_asg = js_function(source, "loadAssignment")
    route = js_function(source, "handleRoute")
    assert "view.gameCode" in load_lib
    assert "/library" in load_lib
    assert "view.gameCode" in load_asg
    assert "/materials" in load_asg
    assert "ASSIGN_GAMES" in route
    assert "loadAssignLibrary()" in route
    assert "loadAssignment()" in route
