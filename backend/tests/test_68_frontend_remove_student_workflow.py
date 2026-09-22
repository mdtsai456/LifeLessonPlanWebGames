"""測試 68：刪除目前選中的學生後，關卡頁會重載下一位的順序。"""

from tests.conftest import frontend_js_source, js_function


def test_remove_student_reloads_workflow(client):
    body = js_function(frontend_js_source(), "removeStudent")
    assert "loadWorkflow()" in body
    assert 'page === "workflow"' in body
