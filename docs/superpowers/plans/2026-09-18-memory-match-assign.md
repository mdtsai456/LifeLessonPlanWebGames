# 記憶配對配置實作計畫

測試使用 `Final/backend` 的 `.venv`。指令是 `uv run pytest`。

**Goal:** 老師能為學生儲存記憶配對 9 格與開場 NPC；沒自訂退回 Default；Unity 讀得到組好的 JSON。

**Architecture:** 新檔 `material.py` 讀寫 `storage/` JSON，規則只套 `MemoryMatch`。`library.py` 加一款遊戲的完整素材庫 GET。Unity 路由組可玩 JSON。前端只在 `MemoryMatch` 配置頁啟用編輯。

**Tech Stack:** FastAPI、MariaDB、vanilla JS、pytest。

## Global Constraints

- 註解使用繁體中文。一句一事。刪除重複說明。
- 測試拆多支檔、由淺入深；編號接 `test_95` 之後。
- 不改 schema。
- 不要污染本機全域 Python／Node。
- 未獲明確要求不要 `git commit`。

## File map

- Create: `Final/backend/storage/GameMaterialDefault/MemoryMatch.json`
- Create: `Final/backend/src/backend/material.py`
- Modify: `Final/backend/src/backend/library.py` — `GET /api/games/{game_code}/library`
- Modify: `Final/backend/src/backend/main.py` — include material router
- Modify: `Final/backend/src/backend/unity.py` — MemoryMatch GET
- Modify: `Final/backend/src/backend/students.py` — 刪學生時刪 material JSON
- Modify: `Final/backend/tests/conftest.py` — 測試幫手與清檔
- Modify: `Final/frontend/js/app.js`、`Final/frontend/css/styles.css`
- Modify: `Final/backend/tests/test_95_frontend_assign_page.py`
- Create: `test_96` 起的 pytest

## 任務

1. Default 種子 + GET（401／200／形狀／等於檔案／缺檔 404）
2. 學生 GET 退回 Default；PUT 驗證 9 格與主題規則；upsert JSON
3. 刪學生刪檔；其他遊戲 400
4. Unity key、組 JSON、缺學生 404
5. 老師頁：MemoryMatch 編輯，其他遊戲仍佔位
