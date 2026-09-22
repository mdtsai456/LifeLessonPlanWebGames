# Image / Model 文案實作計畫

依 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 逐項實作。步驟用 `- [ ]` 記錄進度。

**Goal:** 老師後台使用者看得到的 `2D cube` / `3D model` 改成 `Image` / `Model`，行為不變。

**Architecture:** 只改 `app.js` 畫面字串與檔頭註解。用既有 FastAPI TestClient 讀 `/js/app.js` 做文案檢查。不抽常數、不加 Playwright、不改 API。

**Tech Stack:** 前端 `Final/frontend/js/app.js`；測試 pytest + FastAPI TestClient；在 `Final/backend` 用 `uv run pytest`（專案環境，不碰全域 Python）。

## Global Constraints

- 範圍是方案 C：所有使用者看得到的舊文案都改。
- 作法是方案 1：直接改 `app.js` 字串，不抽常數、不加 Playwright。
- 測試先跑新的前端文案 pytest（B），再跑完整後端測試（A）。
- API 不改。函式名、`kind`、後端檔案都不動。
- 2D 卡片本來沒有類型標籤，不加 `Image`。
- 不加未要求的抽象。註解使用與畫面相同的用語。
- 比對畫面字串，不要只搜 `Image` / `Model`（檔裡還有 `isModel`、`model-viewer` 等）。
- 不要污染本機全域 Python／Node。
- 未獲明確要求不要 `git commit`。

## File map

- Create: `Final/backend/tests/test_22_frontend_labels_new.py` — 確認新文案存在
- Create: `Final/backend/tests/test_23_frontend_labels_old.py` — 確認舊文案不存在
- Modify: `Final/frontend/js/app.js` — 按鈕、表單標題、3D 卡片標籤、檔頭註解

---

### Task 1: 新文案測試（先寫會失敗的測試）

**Files:**
- Create: `Final/backend/tests/test_22_frontend_labels_new.py`
- Test: `Final/backend/tests/test_22_frontend_labels_new.py`

**Interfaces:**
- Consumes: `conftest.py` 的 `client` fixture（`TestClient`）
- Produces: `GET /js/app.js` 必須含 `text: "Image"`、`text: "Model"`、`新增 Image`、`新增 Model`

- [ ] **Step 1: Write the failing test**

建立 `Final/backend/tests/test_22_frontend_labels_new.py`，完整內容如下：

```python
"""第 22 層：前端 app.js 已改成 Image / Model 新文案。"""


def test_app_js_served(client):
    response = client.get("/js/app.js")
    assert response.status_code == 200
    assert "text:" in response.text


def test_type_choice_has_image_button(client):
    source = client.get("/js/app.js").text
    assert 'text: "Image"' in source


def test_type_choice_has_model_button(client):
    source = client.get("/js/app.js").text
    assert 'text: "Model"' in source


def test_add_form_title_image(client):
    source = client.get("/js/app.js").text
    assert "新增 Image" in source


def test_add_form_title_model(client):
    source = client.get("/js/app.js").text
    assert "新增 Model" in source
```

- [ ] **Step 2: Run test to verify new-label cases fail**

在 `Final/backend` 執行：

```powershell
uv run pytest tests/test_22_frontend_labels_new.py -v
```

Expected: `test_app_js_served` PASS（檔案本來就存在）。其餘四則 FAIL，訊息含 `assert 'text: "Image"' in source` 或 `assert "新增 Image" in source` 或 Model 對應字串。不要在這一步改 `app.js`。

---

### Task 2: 舊文案測試（先寫會失敗的測試）

**Files:**
- Create: `Final/backend/tests/test_23_frontend_labels_old.py`
- Test: `Final/backend/tests/test_23_frontend_labels_old.py`

**Interfaces:**
- Consumes: `conftest.py` 的 `client` fixture（`TestClient`）
- Produces: `GET /js/app.js` 不得含 `2D cube`、`3D model`

- [ ] **Step 1: Write the failing test**

建立 `Final/backend/tests/test_23_frontend_labels_old.py`，完整內容如下：

```python
"""第 23 層：前端 app.js 不再出現舊文案 2D cube / 3D model。"""


def test_app_js_has_no_2d_cube(client):
    source = client.get("/js/app.js").text
    assert "2D cube" not in source


def test_app_js_has_no_3d_model(client):
    source = client.get("/js/app.js").text
    assert "3D model" not in source
```

- [ ] **Step 2: Run test to verify it fails**

在 `Final/backend` 執行：

```powershell
uv run pytest tests/test_23_frontend_labels_old.py -v
```

Expected: 兩則都 FAIL。現在 `app.js` 仍有 `2D cube` 與 `3D model`，`assert "2D cube" not in source` 會失敗。不要在這一步改 `app.js`。

---

### Task 3: 改 app.js 畫面字串

**Files:**
- Modify: `Final/frontend/js/app.js`
- Test: `Final/backend/tests/test_22_frontend_labels_new.py`
- Test: `Final/backend/tests/test_23_frontend_labels_old.py`

**Interfaces:**
- Consumes: Task 1／Task 2 的文案斷言
- Produces: 老師看到 Image / Model；`openAdd2dForm`、`openAdd3dForm`、API 路徑不變

- [ ] **Step 1: Write minimal implementation**

只改 `Final/frontend/js/app.js` 這些字串，不要改函式名或 API。

檔頭註解（約第 6 行）由：

```javascript
 * 012 新增素材＝卡片格的 +（先選 2D cube / 3D model）
```

改成：

```javascript
 * 012 新增素材＝卡片格的 +（先選 Image / Model）
```

3D 卡片標籤（約第 533 行）由：

```javascript
      ? el("p", { class: "muted material-kind-label", text: "3D model" })
```

改成：

```javascript
      ? el("p", { class: "muted material-kind-label", text: "Model" })
```

類型按鈕（約第 692–693 行）由：

```javascript
      el("button", { type: "button", text: "2D cube", onclick: () => openAdd2dForm(tag) }),
      el("button", { type: "button", text: "3D model", onclick: () => openAdd3dForm(tag) }),
```

改成：

```javascript
      el("button", { type: "button", text: "Image", onclick: () => openAdd2dForm(tag) }),
      el("button", { type: "button", text: "Model", onclick: () => openAdd3dForm(tag) }),
```

2D 表單標題（約第 763–764 行）由：

```javascript
    "新增 2D cube",
    el("h3", { text: "新增 2D cube" }),
```

改成：

```javascript
    "新增 Image",
    el("h3", { text: "新增 Image" }),
```

3D 表單標題（約第 847–848 行）由：

```javascript
    "新增 3D model",
    el("h3", { text: "新增 3D model" }),
```

改成：

```javascript
    "新增 Model",
    el("h3", { text: "新增 Model" }),
```

不要給 2D 卡片加 `Image` 標籤。不要改 `cube_generate.py`。

- [ ] **Step 2: Run new-label tests to verify they pass（B 前半）**

在 `Final/backend` 執行：

```powershell
uv run pytest tests/test_22_frontend_labels_new.py -v
```

Expected: 五則都 PASS。

- [ ] **Step 3: Run old-label tests to verify they pass（B 後半）**

在 `Final/backend` 執行：

```powershell
uv run pytest tests/test_23_frontend_labels_old.py -v
```

Expected: 兩則都 PASS。

- [ ] **Step 4: Commit（僅在使用者明確要求時）**

未獲明確要求則跳過。若使用者要求 commit：

```powershell
git add Final/frontend/js/app.js Final/backend/tests/test_22_frontend_labels_new.py Final/backend/tests/test_23_frontend_labels_old.py
git commit -m "fix: rename 2D cube and 3D model labels to Image and Model"
```

---

### Task 4: 跑完整後端測試（A）並核對畫面

**Files:**
- Test: `Final/backend/tests/`（既有全部 + test_22 + test_23）

**Interfaces:**
- Consumes: Task 3 改過的 `app.js`
- Produces: 既有 API 測試仍綠；畫面上三處文案已換成 Image / Model

- [ ] **Step 1: Run the full backend suite**

在 `Final/backend` 執行：

```powershell
uv run pytest -v
```

Expected: 全部 PASS。失敗就停，先修再繼續。

- [ ] **Step 2: Check the UI**

啟動後端後打開老師後台素材庫：按 `+`，兩個按鈕是 `Image` 與 `Model`；點進去標題是 `新增 Image` / `新增 Model`；既有 3D 卡片灰色標籤是 `Model`。2D 卡片仍是上傳列，沒有多出 `Image` 標籤。

- [ ] **Step 3: Commit（僅在使用者明確要求時）**

未獲明確要求則跳過。
