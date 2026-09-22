"""測試 36：json_path 跳出 storage/ 時回 400。測完還原。"""

from tests.conftest import first_workflow_default_row, set_workflow_default_path

ESCAPE_PATH = "../static/GameMaterial/tmp/.gitkeep"


def test_workflow_default_escape_storage_is_400(client, auth_headers):
    row = first_workflow_default_row()
    assert row is not None
    original = row["json_path"]
    set_workflow_default_path(row["id"], ESCAPE_PATH)
    try:
        response = client.get("/api/workflow/default", headers=auth_headers)
        assert response.status_code == 400, response.text
    finally:
        set_workflow_default_path(row["id"], original)
