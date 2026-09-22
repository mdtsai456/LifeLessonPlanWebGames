"""測試 153：沒自訂時 Unity 整包沒有頂層 games。每步 material 等於該款 Default。"""

from tests.conftest import UNITY_TEST_KEY, make_student


def test_unity_pack_uses_defaults(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_pack_def")
    unity_headers = {"X-Unity-Key": UNITY_TEST_KEY}
    response = client.get(f"/api/unity/students/{student['id']}", headers=unity_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["studentName"] == student["username"]
    assert "games" not in body
    workflow = body["workflow"]
    assert workflow["storylines"][0]["name"] == "預設"
    default_workflow = client.get("/api/workflow/default", headers=auth_headers)
    assert default_workflow.status_code == 200, default_workflow.text
    default_steps = default_workflow.json()["storylines"][0]["steps"]
    steps = workflow["storylines"][0]["steps"]
    assert [item["game"] for item in steps] == [item["game"] for item in default_steps]
    for step in steps:
        assert step["gameMaterialCustomizationId"] is None
        single = client.get(
            f"/api/unity/students/{student['id']}/games/{step['game']}",
            headers=unity_headers,
        )
        assert single.status_code == 200, single.text
        assert step["material"] == single.json()
