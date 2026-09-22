"""測試 115：儲存記憶配對會 POST 新配置，或 PUT 帶 id 的既有配置。"""

from tests.conftest import frontend_js_source, js_function


def test_save_assignment_puts_memory_materials(client):
    body = js_function(frontend_js_source(), "saveAssignment")
    assert "Start_NPC_Name" in body
    assert "Start_Dialogues" in body
    assert "/materials" in body
    assert 'configId == null ? "POST" : "PUT"' in body
    assert "/materials/${configId}" in body
    assert "itemStaticUrl" in body
    from_api = js_function(frontend_js_source(), "assignmentFromApi")
    assert "itemCodeFromValue" in from_api


def test_handle_route_loads_memory_assignment(client):
    body = js_function(frontend_js_source(), "handleRoute")
    assert "loadAssignLibrary()" in body
    assert "loadAssignment()" in body
