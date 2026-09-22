"""測試 119：正確格全空時，第一個拖入決定主題。畫面格子用大寫代碼。"""

from tests.conftest import frontend_js_source, js_function


def test_place_memory_first_correct_drop_sets_tag(client):
    source = frontend_js_source()
    place = js_function(source, "placeThemeSlots")
    library = js_function(source, "memoryLibraryPanel")
    from_value = js_function(source, "itemCodeFromValue")
    assert "themeSlots.includes(slotKey)" in place
    assert "materialTagCode" in place
    assert "applyThemeTag" in place
    assert "setAssignmentTag" not in library
    assert "function setAssignmentTag" not in source
    assert "toUpperCase" in from_value
