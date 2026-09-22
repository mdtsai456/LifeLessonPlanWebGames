"""測試 49：沒有自訂時，學生關卡等於全站 Default。"""

from tests.conftest import make_student


def test_student_workflow_falls_back_to_default(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_default")
    custom = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    default = client.get("/api/workflow/default", headers=auth_headers)
    assert custom.status_code == 200, custom.text
    assert default.status_code == 200, default.text
    assert custom.json() == default.json()
