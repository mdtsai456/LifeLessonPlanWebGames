"""測試 147：超市購物（購物清單）配置頁是寬版。配置頁有 40 格貨架。配置頁有清單。"""

from tests.conftest import frontend_js_source, js_function


def test_market_assign_page_has_editor(client):
    source = frontend_js_source()
    page = js_function(source, "marketAssignPage")
    shell = js_function(source, "assignShell")
    place = js_function(source, "placeMarket")
    clear_slot = js_function(source, "clearMarketSlot")
    basket = js_function(source, "marketBasketPanel")
    save = js_function(source, "saveAssignment")
    can_save = js_function(source, "assignCanSave")
    slots = js_function(source, "assignSlots")
    empty = js_function(source, "emptyAssignment")
    from_api = js_function(source, "assignmentFromApi")
    css = client.get("/css/styles.css").text
    assert "儲存配置" in shell
    assert "清除全部格子" in shell
    assert "依購物清單順序在貨架上拿取指定商品" in page
    assert "is-wide" in page
    assert "貨架配置" in page
    assert "market-shelves" in page
    assert "market-shelf-scroll" in page
    assert "market-shelf-group" in page
    assert "MARKET_SHELF_GROUPS" in page
    assert "startNpcPanel()" in shell
    assert "memoryLibraryPanel()" in shell
    assert "memory-name-input" not in page
    assert 'placeholder="配置名稱"' not in page
    assert "free_collection" not in source
    assert "購物清單" in basket
    assert "market-basket" in basket
    assert "上移" in basket
    assert "下移" in basket
    assert "addMarketBasket" in basket
    assert "moveMarketBasket" in basket
    assert "removeMarketBasket" in basket
    assert "這個素材已經在其他格子" not in place
    assert "basketOrder" in clear_slot
    assert "MARKET_SHOPPING" in slots
    assert "MARKET_BUDGET" in slots
    assert "MARKET_SLOTS" in slots
    assert "basketOrder" in empty
    assert "prices" in empty
    assert "basketOrder" in from_api
    assert "prices" in from_api
    assert "MARKET_SHOPPING" in can_save
    assert "basketOrder" in can_save
    assert "basketOrder" in save
    assert "prices" in save
    assert "MARKET_SLOTS.filter" in save or ".filter((key) => assignment.items[key])" in save
    assert "${group.prefix}_${index + 1}" in source
    assert "prefix: \"shelf_regular\"" in source
    assert "prefix: \"shelf_veg\"" in source
    assert "prefix: \"shelf_fruit\"" in source
    assert "prefix: \"shelf_meat\"" in source
    assert "prefix: \"shelf_milk\"" in source
    assert "prefix: \"shelf_rice\"" in source
    assert "count: 21" in source
    assert "count: 4" in source
    assert "count: 8" in source
    assert "count: 2" in source
    assert "ASSIGN_GAMES" in source
    assert "MARKET_SHOPPING" in source
    assert "MARKET_BUDGET" in source
    assert ".slot-grid.market-shelves" in css
    market_rule = css.split(".slot-grid.market-shelves", 1)[1].split("}", 1)[0]
    assert "repeat(auto-fill, minmax(7.2rem, 1fr))" in market_rule
    assert ".market-shelf-scroll" in css
    assert ".market-shelf-group" in css
    assert ".market-basket" in css
    media = css.split("@media (max-width: 900px)", 1)[1]
    assert ".slot-grid.market-shelves" in media
    assert "minmax(6.5rem, 1fr)" in media
    preview = js_function(source, "memoryPreviewSrc")
    assert "images/market-board.png" in preview
    assert "images/market-npc.png" in preview


def test_market_preview_images(client):
    board = client.get("/images/market-board.png")
    npc = client.get("/images/market-npc.png")
    assert board.status_code == 200
    assert npc.status_code == 200


def test_assign_page_market_branch(client):
    body = js_function(frontend_js_source(), "assignPage")
    assert "MARKET_SHOPPING" in body
    assert "MARKET_BUDGET" in body
    assert "marketAssignPage(game)" in body
    assert "配置功能稍後提供" in body
