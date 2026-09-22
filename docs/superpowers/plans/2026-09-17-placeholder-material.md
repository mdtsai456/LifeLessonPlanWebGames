# Placeholder 素材實作計畫

依 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 逐項實作。步驟用 `- [ ]` 記錄進度。

**Goal:** 素材庫 `+` 多一個 Placeholder：只填名稱、即時預覽色塊＋首字，入庫走現有「沒圖就寫 SVG」API。

**Architecture:** 只改 `app.js` 與 `.type-choice` CSS。後端 `library.py` / SQL 不動。前端測試讀 `/js/app.js` 函式本體；`test_28` 是既有 API 的字元檢查。

**Tech Stack:** `Final/frontend/js/app.js`、`Final/frontend/css/styles.css`；pytest + FastAPI TestClient；在 `Final/backend` 用 `uv run pytest`（專案 `.venv`，不碰全域 Python）。

## Global Constraints

- 類型按鈕文案是 `Placeholder`（與 Image / Model 一樣英文）。
- 流程：選 Placeholder → 填名稱 → 打字即時預覽 →「加入素材庫」。
- 存檔只 POST `name`。現有 API 寫 `GameMaterial/Shared/MATxxx.svg`。
- 後端不改 `library.py`、不改 SQL。
- 卡片當成 2D：可改名、可之後換圖。不是 Model。
- 空名稱：預覽 `?`；「加入素材庫」disabled。
- 註解使用繁體中文。一句一事。刪除重複說明。
- 測試拆多支檔、由淺入深；`test_26`／`test_27` 只看函式本體。
- 不要污染本機全域 Python／Node。
- 未獲明確要求不要 `git commit`。

## File map

- Create: `Final/backend/tests/test_24_frontend_placeholder_choice.py`
- Create: `Final/backend/tests/test_25_frontend_placeholder_form.py`
- Create: `Final/backend/tests/test_26_frontend_placeholder_save.py`
- Create: `Final/backend/tests/test_27_frontend_placeholder_no_generate.py`
- Create: `Final/backend/tests/test_28_placeholder_svg_label.py`
- Modify: `Final/backend/tests/conftest.py` — 加 `js_function`，給 25／26／27 抽函式本體
- Modify: `Final/frontend/js/app.js` — 第三顆按鈕、表單、`addMaterialByName`
- Modify: `Final/frontend/css/styles.css` — `.type-choice` 三欄
- Spec: `Final/docs/superpowers/specs/2026-09-17-placeholder-material-design.md`

---

### Task 1: 類型選擇有 Placeholder 按鈕（先寫會失敗的測試）

**Files:**
- Create: `Final/backend/tests/test_24_frontend_placeholder_choice.py`
- Test: `Final/backend/tests/test_24_frontend_placeholder_choice.py`

**Interfaces:**
- Consumes: `conftest.py` 的 `client` fixture
- Produces: `GET /js/app.js` 必須含 `text: "Placeholder"`

- [ ] **Step 1: Write the failing test**

建立 `Final/backend/tests/test_24_frontend_placeholder_choice.py`，完整內容如下：

```python
"""第 24 層：選擇素材類型有 Placeholder 按鈕。"""


def test_type_choice_has_placeholder_button(client):
    source = client.get("/js/app.js").text
    assert 'text: "Placeholder"' in source
```

- [ ] **Step 2: Run test to verify it fails**

在 `Final/backend` 執行：

```powershell
uv run pytest tests/test_24_frontend_placeholder_choice.py -v
```

Expected: FAIL，訊息含 `assert 'text: "Placeholder"' in source`。不要在這一步改 `app.js`。

---

### Task 2: Placeholder 表單標題與即時預覽（先寫會失敗的測試）

**Files:**
- Modify: `Final/backend/tests/conftest.py`
- Create: `Final/backend/tests/test_25_frontend_placeholder_form.py`
- Test: `Final/backend/tests/test_25_frontend_placeholder_form.py`

**Interfaces:**
- Consumes: `client`；`js_function(source, name)` 回傳該 function 到下一支 function 之前的字串
- Produces: 有「新增 Placeholder」；`openAddPlaceholderForm` 本體含 `placeholderImage`、`addEventListener("input"`、`saveBtn.disabled`

- [ ] **Step 1: Add js_function helper**

在 `Final/backend/tests/conftest.py` 檔尾加上：

```python
def js_function(source: str, name: str) -> str:
    """取出 app.js 某一支 function 的本體（到下一支 function 之前）。"""
    start = source.find(f"async function {name}(")
    if start < 0:
        start = source.find(f"function {name}(")
    if start < 0:
        raise AssertionError(f"找不到 function {name}")
    next_plain = source.find("\nfunction ", start + 1)
    next_async = source.find("\nasync function ", start + 1)
    ends = [index for index in (next_plain, next_async) if index >= 0]
    end = min(ends) if ends else len(source)
    return source[start:end]
```

- [ ] **Step 2: Write the failing test**

建立 `Final/backend/tests/test_25_frontend_placeholder_form.py`，完整內容如下：

```python
"""第 25 層：Placeholder 表單標題，以及打字即時色塊預覽。"""

from tests.conftest import js_function


def test_add_form_title_placeholder(client):
    source = client.get("/js/app.js").text
    assert "新增 Placeholder" in source


def test_placeholder_form_live_preview(client):
    body = js_function(client.get("/js/app.js").text, "openAddPlaceholderForm")
    assert "placeholderImage" in body
    assert 'addEventListener("input"' in body
    assert "saveBtn.disabled" in body
```

- [ ] **Step 3: Run test to verify it fails**

```powershell
uv run pytest tests/test_25_frontend_placeholder_form.py -v
```

Expected: FAIL（沒有「新增 Placeholder」，或找不到 `openAddPlaceholderForm`）。不要在這一步改 `app.js`。

---

### Task 3: 只 POST name 的 addMaterialByName（先寫會失敗的測試）

**Files:**
- Create: `Final/backend/tests/test_26_frontend_placeholder_save.py`
- Test: `Final/backend/tests/test_26_frontend_placeholder_save.py`

**Interfaces:**
- Consumes: `js_function`、`client`
- Produces: `addMaterialByName` 本體有 `append("name"`，沒有 `temp_id`

- [ ] **Step 1: Write the failing test**

建立 `Final/backend/tests/test_26_frontend_placeholder_save.py`，完整內容如下：

```python
"""第 26 層：Placeholder 入庫只帶名稱，不帶 temp_id。"""

from tests.conftest import js_function


def test_add_material_by_name_posts_only_name(client):
    body = js_function(client.get("/js/app.js").text, "addMaterialByName")
    assert 'append("name"' in body
    assert "temp_id" not in body
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
uv run pytest tests/test_26_frontend_placeholder_save.py -v
```

Expected: FAIL，`找不到 function addMaterialByName`。不要在這一步改 `app.js`。整份 `app.js` 仍有 `addMaterialFromTemp` 的 `temp_id`，那一筆不要拿來斷言。

---

### Task 4: Placeholder 表單不走生成（先寫會失敗的測試）

**Files:**
- Create: `Final/backend/tests/test_27_frontend_placeholder_no_generate.py`
- Test: `Final/backend/tests/test_27_frontend_placeholder_no_generate.py`

**Interfaces:**
- Consumes: `js_function`、`client`
- Produces: `openAddPlaceholderForm` 本體沒有「生成預覽」、沒有 `generate-2d` / `generate-3d`

- [ ] **Step 1: Write the failing test**

建立 `Final/backend/tests/test_27_frontend_placeholder_no_generate.py`，完整內容如下：

```python
"""第 27 層：Placeholder 這條路不生成圖、也不生成模型。"""

from tests.conftest import js_function


def test_placeholder_form_does_not_generate(client):
    body = js_function(client.get("/js/app.js").text, "openAddPlaceholderForm")
    assert "生成預覽" not in body
    assert "generate-2d" not in body
    assert "generate-3d" not in body
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
uv run pytest tests/test_27_frontend_placeholder_no_generate.py -v
```

Expected: FAIL，找不到 `openAddPlaceholderForm`。不要在這一步改 `app.js`。Image / Model 表單仍可有「生成預覽」。

---

### Task 5: 改前端（使測試 24 到 27 通過）

**Files:**
- Modify: `Final/frontend/js/app.js`
- Modify: `Final/frontend/css/styles.css`
- Test: `Final/backend/tests/test_24_frontend_placeholder_choice.py`
- Test: `Final/backend/tests/test_25_frontend_placeholder_form.py`
- Test: `Final/backend/tests/test_26_frontend_placeholder_save.py`
- Test: `Final/backend/tests/test_27_frontend_placeholder_no_generate.py`

**Interfaces:**
- Consumes: Task 1–4 的斷言
- Produces: `openAddPlaceholderForm(tag)`、`addMaterialByName(tag, name, message)`；三欄類型按鈕

- [ ] **Step 1: CSS 三欄**

`Final/frontend/css/styles.css` 的 `.type-choice` 由：

```css
  grid-template-columns: 1fr 1fr;
```

改成：

```css
  grid-template-columns: 1fr 1fr 1fr;
```

- [ ] **Step 2: 檔頭註解**

`Final/frontend/js/app.js` 約第 6 行由：

```javascript
 * 012 新增素材＝卡片格的 +（先選 Image / Model）
```

改成：

```javascript
 * 012 新增素材＝卡片格的 +（先選 Image / Model / Placeholder）
```

- [ ] **Step 3: 第三顆按鈕**

`openAddModal` 的 `.type-choice` 由兩顆改成三顆：

```javascript
      el("button", { type: "button", text: "Image", onclick: () => openAdd2dForm(tag) }),
      el("button", { type: "button", text: "Model", onclick: () => openAdd3dForm(tag) }),
      el("button", { type: "button", text: "Placeholder", onclick: () => openAddPlaceholderForm(tag) }),
```

- [ ] **Step 4: 入庫與表單函式**

放在 `addMaterialFromTemp` 後面、`openAddModal` 前面。不要改 `addMaterialFromTemp`。不要呼叫 `addPreviewActions`（那會帶出「生成預覽」）。

```javascript
async function addMaterialByName(tag, name, message) {
  const body = new FormData();
  body.append("name", name);
  try {
    const created = await api(`/api/tags/${tag.code}/materials`, { method: "POST", body });
    materials.push(created);
    error = "";
    closeModal();
    render();
  } catch (err) {
    message.textContent = err.message;
  }
}

function openAddPlaceholderForm(tag) {
  const nameField = el("input", { placeholder: "例如：木製寶箱" });
  const preview = el("img", { class: "preview-img", alt: "預覽" });
  const message = el("p", { class: "error" });
  const saveBtn = el("button", {
    type: "button",
    text: "加入素材庫",
    onclick: () => {
      const name = nameField.value.trim();
      if (!name) {
        return;
      }
      addMaterialByName(tag, name, message);
    },
  });

  function refreshPreview() {
    const name = nameField.value.trim();
    preview.src = placeholderImage(name, placeholderColor(tag.code));
    saveBtn.disabled = !name;
  }

  nameField.addEventListener("input", refreshPreview);
  refreshPreview();

  showAddPanel(
    "新增 Placeholder",
    el("h3", { text: "新增 Placeholder" }),
    el("label", {}, "素材名稱", nameField),
    preview,
    message,
    el(
      "div",
      { class: "modal-actions" },
      saveBtn,
      el("button", { class: "ghost", type: "button", text: "返回", onclick: () => openAddModal(tag) }),
    ),
  );
  queueMicrotask(() => nameField.focus());
}
```

`refreshPreview()` 在一開始會跑一次：空名稱時 `placeholderImage` 畫 `?`，且 `saveBtn.disabled = true`。

- [ ] **Step 5: Run frontend tests 24–27**

```powershell
uv run pytest tests/test_24_frontend_placeholder_choice.py tests/test_25_frontend_placeholder_form.py tests/test_26_frontend_placeholder_save.py tests/test_27_frontend_placeholder_no_generate.py -v
```

Expected: 全部 PASS。

- [ ] **Step 6: Commit（僅在使用者明確要求時）**

未獲明確要求則跳過。

---

### Task 6: API 寫出的 SVG 含名稱首字（既有後端，應已綠）

**Files:**
- Create: `Final/backend/tests/test_28_placeholder_svg_label.py`
- Test: `Final/backend/tests/test_28_placeholder_svg_label.py`

**Interfaces:**
- Consumes: `make_tag`、`auth_headers`、`POST /api/tags/{tag}/materials`
- Produces: 201、`image_url` 以 `.svg` 結尾、靜態檔 `<text>` 內容是名稱第一個字

名稱必須 `zz_pytest_` 開頭，cleanup 才會刪。因此首字是 `z`，不是中文。這仍是在測 `write_placeholder` 的 `name.strip()[:1]`。

- [ ] **Step 1: Write the test**

建立 `Final/backend/tests/test_28_placeholder_svg_label.py`，完整內容如下：

```python
"""第 28 層：沒上傳圖時，後端 SVG 色塊的字是名稱首字。"""

from tests.conftest import make_tag


def test_placeholder_svg_uses_first_character(client, auth_headers):
    tag = make_tag(client, auth_headers)
    name = "zz_pytest_木箱"
    created = client.post(
        f"/api/tags/{tag}/materials",
        headers=auth_headers,
        data={"name": name},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["image_url"].endswith(".svg")
    assert "model_url" not in body

    static = client.get(body["image_url"])
    assert static.status_code == 200
    label = name.strip()[:1]
    assert f">{label}</text>" in static.text
```

- [ ] **Step 2: Run test — 預期 PASS（不要改 library.py）**

```powershell
uv run pytest tests/test_28_placeholder_svg_label.py -v
```

Expected: PASS。若 FAIL，停下來查 `write_placeholder`，不要為了讓測試過而改 API 行為。

- [ ] **Step 3: Commit（僅在使用者明確要求時）**

未獲明確要求則跳過。

---

### Task 7: 完整測試與畫面核對

**Files:**
- Test: `Final/backend/tests/`（既有全部 + test_24–28）

**Interfaces:**
- Consumes: Task 5 的前端、Task 6 的 API 斷言
- Produces: 全綠；畫面上第三條路可用

- [ ] **Step 1: Run the full backend suite**

在 `Final/backend` 執行：

```powershell
uv run pytest -v
```

Expected: 全部 PASS。失敗就停，先修再繼續。

- [ ] **Step 2: Check the UI**

後端已在 8001 的話，打開素材庫按 `+`：

1. 三顆並排：`Image`　`Model`　`Placeholder`
2. 點 Placeholder，標題「新增 Placeholder」
3. 還沒打字：色塊是 `?`，「加入素材庫」不能按
4. 打「足球」：色塊變成「足」，可以加入
5. 加入後卡片是色塊圖，不是 Model；可改名

不要打 generate API。不要在 Network 裡看到 `temp_id`。

- [ ] **Step 3: Commit（僅在使用者明確要求時）**

未獲明確要求則跳過。
