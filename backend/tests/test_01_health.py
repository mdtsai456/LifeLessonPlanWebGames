"""測試 1：服務是否已啟動。資料庫是否可連線。尚未測登入。"""


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_db_check(client):
    response = client.get("/api/db-check")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert "MariaDB" in body["version"]


def test_frontend_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LifeLessonPlan" in response.text
    assert 'id="modal-root"' in response.text
    assert "model-viewer/3.5.0/model-viewer.min.js" in response.text
