"""測試 164：未帶 token 的 db-check 仍是 200。回應沒有 database。回應沒有 error。"""


def test_db_check_hides_names(client):
    response = client.get("/api/db-check")
    assert response.status_code == 200
    body = response.json()
    assert "database" not in body
    assert "error" not in body
