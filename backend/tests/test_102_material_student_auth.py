"""測試 102：學生素材 API 要登入。"""


def test_student_material_get_needs_login(client):
    response = client.get("/api/students/1/games/MemoryMatch/materials")
    assert response.status_code == 401


def test_student_material_post_needs_login(client):
    response = client.post("/api/students/1/games/MemoryMatch/materials", json={})
    assert response.status_code == 401
