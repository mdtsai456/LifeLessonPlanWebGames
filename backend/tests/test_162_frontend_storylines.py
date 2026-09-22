"""測試 162：配置頁建立使用 POST。配置頁更新使用帶 id 的 PUT。關卡頁送出故事線與素材 id。"""

from tests.conftest import js_function


def test_assign_save_posts_and_puts_with_id(client):
    body = js_function("", "saveAssignment")
    assert 'configId == null ? "POST" : "PUT"' in body
    assert "/api/students/${studentId}/games/${gameCode}/materials" in body
    assert "/api/students/${studentId}/games/${gameCode}/materials/${configId}" in body


def test_workflow_save_sends_storylines(client):
    payload = js_function("", "workflowPayload")
    assert "storylines:" in payload
    assert "gameMaterialCustomizationId: step.gameMaterialCustomizationId" in payload
    save = js_function("", "saveWorkflow")
    assert "workflowPayload()" in save
    assert "/api/students/${studentId}/workflow" in save
