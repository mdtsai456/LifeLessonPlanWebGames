# Placeholder 素材（色塊＋首字）

日期：2026-09-17  
狀態：spec／計畫已核准，尚未改程式

## 目標

老師按素材庫 `+` 時，除了 Image / Model，多一個 **Placeholder**：不用生成圖、也不用 3D，只填名稱，卡片用色塊＋名稱首字。

## 決策摘要

| 項目 | 決定 |
|------|------|
| 類型按鈕文案 | `Placeholder`（與 Image / Model 一樣英文） |
| 流程 | 選 Placeholder → 填名稱 → 打字即時預覽色塊 →「加入素材庫」 |
| 存檔 | 只 POST `name`。現有 API 會寫 `GameMaterial/Shared/MATxxx.svg` |
| 後端 | **不改** `library.py`、不改 SQL |
| 卡片種類 | 當成 2D：可改名、可之後換圖。不是 Model |
| 空名稱 | 預覽顯示 `?`；「加入素材庫」disabled |
| 程式風格 | 註解使用繁體中文。一句一事。刪除重複說明。 |
| 測試 | 拆多支 pytest、由淺入深；前端測 `/js/app.js` 字串 |

## 非目標

- 改資料表、讓 `file_path` 可空
- 卡片只用前端 data URI、磁碟不寫檔
- 把 Placeholder 塞進 Image 表單
- 瀏覽器點擊／E2E
- 改 generate-2d / generate-3d

## 使用流程

1. 素材庫按 `+` →「選擇素材類型」三顆並排：`Image`　`Model`　`Placeholder`。
2. 點 Placeholder。標題：`新增 Placeholder`。
3. 一個名稱欄位。打字時下方立刻顯示色塊＋首字（現有 `placeholderImage`）。名稱清空時顯示 `?`。
4. 名稱空白（trim 後空）時「加入素材庫」不能按。
5. 「返回」回到三選一。沒有「生成預覽」，也不打 generate API。
6. 「加入素材庫」：`FormData` 只帶 `name`，`POST /api/tags/{tag.code}/materials`。
7. 成功後關 modal、卡片出現在該分類。之後行為與現有圖片素材相同。

## 畫面與前端

改 `Final/frontend/js/app.js`、`Final/frontend/css/styles.css`。

- `openAddModal` 第三顆按鈕 → `openAddPlaceholderForm(tag)`。
- 新表單函式不要複用 Image / Model 的「生成預覽」動作列。
- 還原／新增 `addMaterialByName`：只 `append("name", name)`，不要 `temp_id`、不要上傳檔。
- 檔頭註解改成：新增素材先選 Image / Model / Placeholder。
- `.type-choice` 改三欄。

預覽用現有：

```javascript
placeholderImage(name, placeholderColor(tag.code))
```

名稱 `input` 事件更新 `img.src`，並依 trim 後是否有字切換「加入素材庫」的 `disabled`。

## 儲存

現有後端（不動）：

```
沒有 temp_id、也沒有上傳圖
  → write_placeholder()
  → GameMaterial/Shared/MATxxx.svg
  → JSON 回 image_url（不是 model_url）
```

圖片載入失敗時，前端用 data URI 顯示佔位圖。這與新增 Placeholder 不同。這次入庫後有真實 SVG，卡片應載 `/static/GameMaterial/Shared/MATxxx.svg`。

## 測試

現有 `test_09` 的「沒圖也能新增」保留。新測試從第 24 層起，一支檔一件事：

| 檔案 | 在測什麼 |
|------|----------|
| `tests/test_24_frontend_placeholder_choice.py` | `app.js` 有 `text: "Placeholder"` |
| `tests/test_25_frontend_placeholder_form.py` | 有「新增 Placeholder」；有 `placeholderImage` 做預覽 |
| `tests/test_26_frontend_placeholder_save.py` | 有 `addMaterialByName`；該函式只 append name，沒有 `temp_id` |
| `tests/test_27_frontend_placeholder_no_generate.py` | Placeholder 表單函式裡沒有「生成預覽」、沒有 `generate-2d` / `generate-3d` |
| `tests/test_28_placeholder_svg_label.py` | 只 POST name → 201、`image_url` 以 `.svg` 結尾、靜態檔含名稱首字 |

前端測試方式與 `test_22` 相同：`client.get("/js/app.js")` 看原始碼字串。  
`test_26`／`test_27` 只斷言對應函式本體（`addMaterialByName`、`openAddPlaceholderForm`），不要拿整份 `app.js` 來禁止 `temp_id` 或 generate（Image / Model 仍會用）。  
`test_28` 用現有 `make_tag` + 登入 header，名稱用 `zz_pytest_` 前綴以免污染種子資料。

TDD：先寫會失敗的測試，再改前端／（僅 test_28 所需的）確認後端行為已存在。

## 架構

```
老師後台 +
  → 選 Placeholder
  → 填名稱（即時 placeholderImage 預覽）
  → POST /api/tags/{tag}/materials   Form: name
       → write_placeholder
       → Shared/MATxxx.svg
```
