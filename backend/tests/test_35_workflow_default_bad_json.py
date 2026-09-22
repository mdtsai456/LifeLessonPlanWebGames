"""測試 35：JSON 損壞時回 500。測完還原。"""

from tests.conftest import (
    first_workflow_default_row,
    set_workflow_default_path,
    write_pytest_workflow_file,
)


def test_workflow_default_bad_json_is_500(client, auth_headers):
    row = first_workflow_default_row()
    assert row is not None
    original = row["json_path"]
    with write_pytest_workflow_file("zz_pytest_bad.json", "{ not json"):
        set_workflow_default_path(row["id"], "GameWorkflowDefault/zz_pytest_bad.json")
        try:
            response = client.get("/api/workflow/default", headers=auth_headers)
            assert response.status_code == 500, response.text
        finally:
            set_workflow_default_path(row["id"], original)
