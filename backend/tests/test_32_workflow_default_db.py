"""測試 32：API 回傳內容等於資料庫 json_path 指向的檔。"""

import json

from backend.database import STORAGE_DIR, connect_db


def test_workflow_default_matches_db_file(client, auth_headers):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT json_path FROM GameWorkflowDefault ORDER BY id LIMIT 1")
            row = cursor.fetchone()
    finally:
        connection.close()
    assert row is not None
    path = STORAGE_DIR / row["json_path"]
    expected = json.loads(path.read_text(encoding="utf-8"))

    response = client.get("/api/workflow/default", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json() == expected
