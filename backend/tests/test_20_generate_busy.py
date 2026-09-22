"""測試 20：2D 與 3D 共用一把鎖。忙碌時回 429。"""

from backend.gpu_job import release, try_acquire
from tests.conftest import make_tag


def test_generate_while_busy_is_429(client, auth_headers):
    tag = make_tag(client, auth_headers)
    try_acquire()
    try:
        two_d = client.post(
            f"/api/tags/{tag}/generate-2d",
            headers=auth_headers,
            json={"objectName": "zz_pytest_忙"},
        )
        three_d = client.post(
            f"/api/tags/{tag}/generate-3d",
            headers=auth_headers,
            json={"prompt": "a chair"},
        )
        assert two_d.status_code == 429
        assert three_d.status_code == 429
    finally:
        release()
