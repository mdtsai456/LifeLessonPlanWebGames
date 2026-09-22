"""測試 54：自訂關卡 JSON 不能從 /static 直接下載。"""

from tests.conftest import TEST_USERNAME, make_student


def test_student_workflow_not_on_static(client, auth_headers):
    make_student(client, auth_headers, "zz_pytest_student_static")
    response = client.get(
        f"/static/GameWorkflowCustomization/{TEST_USERNAME}/zz_pytest_student_static/workflow.json"
    )
    assert response.status_code != 200
