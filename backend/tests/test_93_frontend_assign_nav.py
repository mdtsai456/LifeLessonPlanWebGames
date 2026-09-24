"""測試 93：側欄在關卡配置與素材庫之間有遊戲配置。每款遊戲列出代號與 id。每款遊戲可新增。"""

from tests.conftest import frontend_js_source, js_function


def test_nav_has_assign_section_between_workflow_and_materials(client):
    body = js_function(frontend_js_source(), "renderNav")
    workflow = body.index('text: "關卡流程"')
    assign = body.index('text: "遊戲配置"')
    materials = body.index('text: "素材庫"')
    assert workflow < assign < materials
    assert "assignGameBlock(game)" in body
    assert 'navButton(game, "materials")' in body
    assert 'navButton(game, "assign")' not in body


def test_nav_button_uses_page_and_game_code(client):
    body = js_function(frontend_js_source(), "navButton")
    assert "goTo(`${page}/${game.code}`)" in body
    assert "route.page === page" in body


def test_assign_game_block_lists_code_and_id(client):
    body = js_function(frontend_js_source(), "assignGameBlock")
    assert "nav-config-item" in body
    assert "nav-config-add" in body
    assert "`${game.code} ${config.id}`" in body
    assert 'draggable: "true"' in body
