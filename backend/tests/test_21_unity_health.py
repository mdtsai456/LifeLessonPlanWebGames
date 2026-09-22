"""測試 21：Unity 健康檢查只接受 X-Unity-Key。"""

from tests.conftest import UNITY_TEST_KEY


def test_unity_health_ok_with_key(client):
    response = client.get("/api/unity/health", headers={"X-Unity-Key": UNITY_TEST_KEY})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unity_health_missing_key_is_401(client):
    response = client.get("/api/unity/health")
    assert response.status_code == 401


def test_unity_health_wrong_key_is_401(client):
    response = client.get("/api/unity/health", headers={"X-Unity-Key": "wrong-key-value"})
    assert response.status_code == 401


def test_unity_health_unset_key_is_401(client, monkeypatch):
    monkeypatch.setenv("UNITY_API_KEY", "")
    response = client.get(
        "/api/unity/health",
        headers={"X-Unity-Key": UNITY_TEST_KEY},
    )
    assert response.status_code == 401
