"""測試 38：無效 token 也回 401。"""


def test_workflow_default_wrong_token_is_401(client):
    response = client.get(
        "/api/workflow/default",
        headers={"Authorization": "Bearer zz_pytest_not_a_real_token"},
    )
    assert response.status_code == 401
