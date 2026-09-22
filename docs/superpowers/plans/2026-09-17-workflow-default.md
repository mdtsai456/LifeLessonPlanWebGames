# GameWorkflowDefault 讀取 API 實作計畫

依 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 逐項實作。步驟用 `- [ ]` 記錄進度。

**Goal:** 登入後 `GET /api/workflow/default` 回傳 `storage/GameWorkflowDefault/workflow.json`。

**Architecture:** 新檔 `workflow.py` 讀 `GameWorkflowDefault.json_path`，接到 `STORAGE_DIR`。不把此讀檔寫入 `library.py`。JSON 不走 `/static`。

**Tech Stack:** FastAPI；pytest + TestClient；在 `Final/backend` 用 `uv run pytest`（專案 `.venv`，不碰全域 Python）。

## Global Constraints

- 註解使用繁體中文。一句一事。刪除重複說明。
- 測試拆多支檔、由淺入深；編號接 `test_28` 之後。
- 不改 schema、不做 Customization、不動前端。
- 測試不要新增第二列 `GameWorkflowDefault`（`ORDER BY id LIMIT 1`）。
- 不要污染本機全域 Python／Node。
- 未獲明確要求不要 `git commit`。

## File map

- Create: `Final/backend/storage/GameWorkflowDefault/workflow.json`
- Create: `Final/backend/src/backend/workflow.py`
- Create: `Final/backend/tests/test_29_workflow_default_auth.py`
- Create: `Final/backend/tests/test_30_workflow_default_ok.py`
- Create: `Final/backend/tests/test_31_workflow_default_shape.py`
- Create: `Final/backend/tests/test_32_workflow_default_db.py`
- Create: `Final/backend/tests/test_33_workflow_default_missing_file.py`
- Create: `Final/backend/tests/test_34_workflow_default_not_static.py`
- Modify: `Final/backend/src/backend/database.py` — `STORAGE_DIR`
- Modify: `Final/backend/src/backend/main.py` — include workflow router

---

### Task 1: 種子檔與 STORAGE_DIR

- [x] `STORAGE_DIR = BACKEND_DIR / "storage"`
- [x] 寫入與 Jack 相同的五關 `workflow.json`

### Task 2: GET API

- [x] `workflow.py`：登入、讀 json_path、路徑不可跳出 storage、缺檔 404
- [x] `main.py` 掛上 router

### Task 3: 測試

- [x] `test_29` 沒 token → 401
- [x] `test_30` 有 token → 200 且有 `games`
- [x] `test_31` 五款 slug、`order` 1–5，沒有 `configId`
- [x] `test_32` 回應等於 json_path 指向的檔
- [x] `test_33` 暫時改 path 指到不存在檔 → 404，再還原
- [x] `test_34` `/static/GameWorkflowDefault/workflow.json` 不是 200
