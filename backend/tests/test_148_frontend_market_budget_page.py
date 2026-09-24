"""測試 148：超市購物預算模式配置頁有預算輸入。超市購物預算模式配置頁沒有購物清單。"""

from tests.conftest import frontend_js_source, js_function


def test_market_budget_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "marketAssignPage")
    shell = js_function(source, "assignShell")
    budget = js_function(source, "marketBudgetField")
    basket = js_function(source, "marketBasketPanel")
    save = js_function(source, "saveAssignment")
    can_save = js_function(source, "assignCanSave")
    load_lib = js_function(source, "loadAssignLibrary")
    from_api = js_function(source, "assignmentFromApi")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "在預算內選購貨架上的商品" in page
    assert "is-wide" in page
    assert "market-shelves" in page
    assert "MARKET_BUDGET" in page
    assert "marketBudgetField()" in page
    assert "marketBasketPanel()" in page
    assert "startNpcPanel()" in shell
    assert "memoryLibraryPanel()" in shell
    assert "memory-name-input" not in page
    assert "market-budget" in budget
    assert "預算" in budget
    assert "market-basket" not in budget
    assert "basketOrder" not in budget
    assert "market-basket" in basket
    assert "MARKET_BUDGET" in can_save
    assert "assignment.budget" in can_save
    assert "budget" in from_api
    assert "payloadBody.budget" in save
    assert "MARKET_BUDGET" in save
    assert "view.gameCode" in load_lib
    assert "/library" in load_lib
    assert ".slot-grid.market-shelves" in css
    market_rule = css.split(".slot-grid.market-shelves", 1)[1].split("}", 1)[0]
    assert "repeat(auto-fill, minmax(7.2rem, 1fr))" in market_rule
    assert ".market-budget" in css
    media = css.split("@media (max-width: 900px)", 1)[1]
    assert ".slot-grid.market-shelves" in media
    assert "minmax(6.5rem, 1fr)" in media
    preview = js_function(source, "memoryPreviewSrc")
    assert "images/market-board.png" in preview
    assert "images/market-npc.png" in preview


def test_market_budget_preview_images(client):
    board = client.get("/images/market-board.png")
    npc = client.get("/images/market-npc.png")
    assert board.status_code == 200
    assert npc.status_code == 200


def test_assign_page_market_budget_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "MARKET_SHOPPING" in body
    assert "MARKET_BUDGET" in body
    assert "marketAssignPage(game)" in body
