"""測試 160：故事線可少於六款。故事線可重複遊戲。故事線可共用素材。錯 id 回 400。空線回 400。order 不連續回 400。舊 games 檔 GET 不改磁碟。"""

import json

from backend.database import connect_db
from tests.conftest import STORAGE_DIR, make_memory_config, make_student, make_vacuum_config


def _put(client, headers, student_id: int, body: dict):
    return client.put(
        f"/api/students/{student_id}/workflow",
        headers=headers,
        json=body,
    )


def test_fewer_than_six_games_is_ok(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_short")
    body = {
        "startNpcName": "開場",
        "startDialogues": ["先選一條"],
        "storylines": [
            {
                "name": "只有兩步",
                "order": 1,
                "steps": [
                    {
                        "game": "MarketShopping",
                        "gameMaterialCustomizationId": None,
                        "order": 1,
                        "endNpcName": "",
                        "endDialogues": [],
                    },
                    {
                        "game": "MemoryMatch",
                        "gameMaterialCustomizationId": None,
                        "order": 2,
                        "endNpcName": "",
                        "endDialogues": [],
                    },
                ],
            }
        ],
    }
    saved = _put(client, auth_headers, int(student["id"]), body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == body


def test_same_game_can_repeat(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_repeat")
    saved = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "startNpcName": "",
            "startDialogues": [],
            "storylines": [
                {
                    "name": "重複",
                    "order": 1,
                    "steps": [
                        {
                            "game": "MarketShopping",
                            "gameMaterialCustomizationId": None,
                            "order": 1,
                            "endNpcName": "",
                            "endDialogues": [],
                        },
                        {
                            "game": "MarketShopping",
                            "gameMaterialCustomizationId": None,
                            "order": 2,
                            "endNpcName": "第二次",
                            "endDialogues": ["再買一次"],
                        },
                    ],
                }
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    steps = saved.json()["storylines"][0]["steps"]
    assert [item["game"] for item in steps] == ["MarketShopping", "MarketShopping"]


def test_steps_share_one_material_id(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_share")
    payload = make_memory_config(client, auth_headers)
    created = client.post(
        f"/api/students/{student['id']}/games/MemoryMatch/materials",
        headers=auth_headers,
        json=payload,
    )
    assert created.status_code == 201, created.text
    material_id = created.json()["id"]
    saved = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "startNpcName": "",
            "startDialogues": [],
            "storylines": [
                {
                    "name": "共用",
                    "order": 1,
                    "steps": [
                        {
                            "game": "MemoryMatch",
                            "gameMaterialCustomizationId": material_id,
                            "order": 1,
                            "endNpcName": "",
                            "endDialogues": [],
                        },
                        {
                            "game": "MemoryMatch",
                            "gameMaterialCustomizationId": material_id,
                            "order": 2,
                            "endNpcName": "",
                            "endDialogues": [],
                        },
                    ],
                }
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    ids = [
        item["gameMaterialCustomizationId"]
        for item in saved.json()["storylines"][0]["steps"]
    ]
    assert ids == [material_id, material_id]


def test_null_material_id_is_kept(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_null")
    saved = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "startNpcName": "",
            "startDialogues": [],
            "storylines": [
                {
                    "name": "預設素材",
                    "order": 1,
                    "steps": [
                        {
                            "game": "MemoryMatch",
                            "gameMaterialCustomizationId": None,
                            "order": 1,
                            "endNpcName": "",
                            "endDialogues": [],
                        }
                    ],
                }
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["storylines"][0]["steps"][0]["gameMaterialCustomizationId"] is None


def test_wrong_material_id_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_badid")
    vacuum = make_vacuum_config(client, auth_headers)
    created = client.post(
        f"/api/students/{student['id']}/games/PairVacuum/materials",
        headers=auth_headers,
        json=vacuum,
    )
    assert created.status_code == 201, created.text
    missing = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {
                    "name": "錯的",
                    "order": 1,
                    "steps": [
                        {
                            "game": "MemoryMatch",
                            "gameMaterialCustomizationId": 999999999,
                            "order": 1,
                        }
                    ],
                }
            ]
        },
    )
    assert missing.status_code == 400
    wrong_game = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {
                    "name": "錯遊戲",
                    "order": 1,
                    "steps": [
                        {
                            "game": "MemoryMatch",
                            "gameMaterialCustomizationId": created.json()["id"],
                            "order": 1,
                        }
                    ],
                }
            ]
        },
    )
    assert wrong_game.status_code == 400


def test_empty_storyline_is_400(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_empty")
    no_lines = _put(
        client,
        auth_headers,
        int(student["id"]),
        {"startNpcName": "", "startDialogues": [], "storylines": []},
    )
    assert no_lines.status_code == 400
    no_steps = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {"name": "空的", "order": 1, "steps": []},
            ]
        },
    )
    assert no_steps.status_code == 400
    blank_name = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {
                    "name": "   ",
                    "order": 1,
                    "steps": [{"game": "MemoryMatch", "order": 1}],
                }
            ]
        },
    )
    assert blank_name.status_code == 400


def test_order_must_be_consecutive(client, auth_headers):
    student = make_student(client, auth_headers, "zz_pytest_student_line_order")
    step_gap = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {
                    "name": "步驟跳號",
                    "order": 1,
                    "steps": [
                        {"game": "MemoryMatch", "order": 1},
                        {"game": "PairVacuum", "order": 3},
                    ],
                }
            ]
        },
    )
    assert step_gap.status_code == 400
    line_gap = _put(
        client,
        auth_headers,
        int(student["id"]),
        {
            "storylines": [
                {
                    "name": "第一條",
                    "order": 1,
                    "steps": [{"game": "MemoryMatch", "order": 1}],
                },
                {
                    "name": "第三條",
                    "order": 3,
                    "steps": [{"game": "PairVacuum", "order": 1}],
                },
            ]
        },
    )
    assert line_gap.status_code == 400


def test_legacy_games_file_get_keeps_disk(client, auth_headers, test_teacher):
    student = make_student(client, auth_headers, "zz_pytest_student_line_legacy")
    legacy = {
        "games": [
            {
                "game": "MemoryMatch",
                "order": 1,
                "endNpcName": "阿姨",
                "endDialogues": ["舊的閉場"],
            }
        ]
    }
    relative = (
        f"GameWorkflowCustomization/{test_teacher['username']}/"
        f"{student['username']}/workflow.json"
    )
    path = STORAGE_DIR / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before = path.read_bytes()
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO GameWorkflowCustomization (teacher_id, student_id, json_path)
                VALUES (%s, %s, %s)
                """,
                (test_teacher["id"], student["id"], relative),
            )
        connection.commit()
    finally:
        connection.close()

    loaded = client.get(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
    )
    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == legacy
    rejected = client.put(
        f"/api/students/{student['id']}/workflow",
        headers=auth_headers,
        json=legacy,
    )
    assert rejected.status_code == 400
    assert path.read_bytes() == before
