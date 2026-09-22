"""測試 33：json_path 指向不存在的檔時回 404。測完還原。"""

from tests.conftest import first_workflow_default_row, set_workflow_default_path

MISSING_PATH = "GameWorkflowDefault/zz_pytest_missing.json"


def test_workflow_default_missing_file_is_404(client, auth_headers):
    row = first_workflow_default_row()
    assert row is not None
    original = row["json_path"]
    set_workflow_default_path(row["id"], MISSING_PATH)
    try:
        response = client.get("/api/workflow/default", headers=auth_headers)
        assert response.status_code == 404, response.text
    finally:
        set_workflow_default_path(row["id"], original)
