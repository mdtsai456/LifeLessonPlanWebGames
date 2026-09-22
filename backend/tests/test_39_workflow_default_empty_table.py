"""測試 39：表沒有列時改讀約定檔名。測完把列插回。"""

from backend.database import connect_db
from tests.conftest import first_workflow_default_row


def _all_default_rows() -> list[dict]:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, json_path FROM GameWorkflowDefault ORDER BY id")
            return cursor.fetchall()
    finally:
        connection.close()


def _delete_all_default_rows() -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM GameWorkflowDefault")
        connection.commit()
    finally:
        connection.close()


def _restore_default_rows(rows: list[dict]) -> None:
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            for row in rows:
                cursor.execute(
                    "INSERT INTO GameWorkflowDefault (id, json_path) VALUES (%s, %s)",
                    (row["id"], row["json_path"]),
                )
        connection.commit()
    finally:
        connection.close()


def test_workflow_default_empty_table_uses_fallback(client, auth_headers):
    saved = _all_default_rows()
    assert saved
    assert first_workflow_default_row() is not None
    _delete_all_default_rows()
    try:
        response = client.get("/api/workflow/default", headers=auth_headers)
        assert response.status_code == 200, response.text
        assert response.json()["storylines"]
    finally:
        _restore_default_rows(saved)
