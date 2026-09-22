# 001／002／003：Text2Image、Trellis、Unity 探針

日期：2026-09-17  
狀態：確認規格後才實作。

## 目標

在 `Final` 老師後台接上參考專案已能用的三件事，並符合現有 MariaDB 表、現有靜態目錄。

| 編號 | 內容 |
|------|------|
| 001 | Text 2 Image：填物件名稱 → 生成 PNG 預覽 → 加入素材庫 |
| 002 | Text 2 Model：填標題與描述 → 生成 GLB 預覽（可拖曳旋轉）→ 加入素材庫 |
| 003 | 區網機器用 `UNITY_API_KEY` 打探針；第一版**不讀**素材、也不做學生遊戲配置 |

## 決策摘要

| 項目 | 決定 |
|------|------|
| 架構 | 拆小檔：`gpu_job.py`、`cube_generate.py`、`trellis_generate.py`、Unity 探針。不把這些函式寫入 `library.py`。不 import `References/material` |
| SQL | **不改表結構**。對 `GameMaterial` 做既有 INSERT／DELETE；`file_path` 寫相對 `static/` 的路徑 |
| 正式檔 | `Final/backend/static/GameMaterial/Shared/MATxxx.png` 或 `.glb` |
| 暫存 | `Final/backend/static/GameMaterial/tmp/{tempId}.png` 或 `.glb`；按「加入素材庫」才搬進 Shared |
| 真生成 | `.env` 沒開 MOCK 就呼叫 text2image／Trellis |
| 測試 | pytest 在 `conftest` 強制 MOCK，不碰 GPU |
| 3D 操作 | `model-viewer` 的 `camera-controls` + `auto-rotate`（轉模型、拖視角）。**不做**把卡片拖進遊戲格子 |
| Unity | 只做 `GET /api/unity/health` + `X-Unity-Key` |
| 程式風格 | 註解使用繁體中文。一句一事。刪除重複說明。測試拆很多支檔、由淺入深 |

## 非目標

- 每位老師對不同學生的遊戲配置（資料庫雖有 `Student`／`GameMaterialCustomization`）。本文件不寫該 API。
- Unity 讀素材庫或讀配置
- 改 SQL、加 `kind`／`model_path` 欄位
- 非同步 job 佇列與輪詢
- 把 Trellis／text2image 原始碼或權重複製進 Final
- 老師自訂 2D 風格 prompt、seed、解析度
- 2D 與 3D 同時跑（共用一個鎖。同一時間只跑一個生成。）

## 使用流程

### 2D cube

1. 素材庫按 `+` → 2D cube。
2. 填物件名稱（同時當生圖輸入與素材標題）。
3. 「生成預覽」：後端寫暫存 PNG；前端顯示圖片。按鈕顯示「生成中…」，可能要幾分鐘，不要重整。
4. 「加入素材庫」：搬到 Shared、INSERT `GameMaterial`、掛上該分類。
5. 入庫後卡片與現有圖片素材相同：可改名、可換圖。

### 3D model

1. 素材庫按 `+` → 3D model。
2. 填標題與英文描述；送出時自動加上 `(low poly, with smooth curve)`（已含則不重複）。
3. 「生成預覽」：後端寫暫存 GLB；前端用 `model-viewer` 顯示，可拖曳旋轉、滾輪縮放、閒置自轉。
4. 「加入素材庫」：搬到 Shared、INSERT、掛分類。
5. 入庫後卡片同樣用 `model-viewer`，不提供「更換圖片」。

### Unity 探針

區網別台：

```http
GET http://{主機區網IP}:{port}/api/unity/health
Header: X-Unity-Key: <UNITY_API_KEY>
```

key 對 → 200 `{"status":"ok"}`；沒帶或帶錯 → 401。

## 架構

```
老師後台 app.js
  → POST /api/tags/{tag}/generate-2d  {objectName}
       → cube_generate（MOCK 或 TEXT2IMAGE_PYTHON 子行程跑 generate.py）
       → static/GameMaterial/tmp/{tempId}.png
  → POST /api/tags/{tag}/generate-3d  {prompt}
       → trellis_generate（MOCK 或本機 Trellis）
       → static/GameMaterial/tmp/{tempId}.glb
  → POST /api/tags/{tag}/materials  Form: name + temp_id
       → 搬到 Shared/MATxxx.*
       → INSERT GameMaterial + GameMaterialTag

Unity
  → GET /api/unity/health  Header X-Unity-Key
```

2D 與 3D 共用 `gpu_job.py` 非阻塞鎖：拿不到就 `BusyError` → 429。

適配層不把 torch／SDXL 載進素材 CRUD。text2image 用獨立 venv 子行程；Trellis 沿用參考專案的 lazy load。

檔案類型用 `file_path` 副檔名判斷：`.glb` 當 3D（JSON 給 `model_url`），其餘當圖片（`image_url`）。不改資料表。

## API

老師端都要 Bearer token。

### `POST /api/tags/{tag_code}/generate-2d`

Body：`{"objectName": "木製寶箱"}`  
成功：`{"tempId": "...", "imageUrl": "/static/GameMaterial/tmp/{tempId}.png"}`

### `POST /api/tags/{tag_code}/generate-3d`

Body：`{"prompt": "a red chair"}`（後端再加風格詞）  
成功：`{"tempId": "...", "modelUrl": "/static/GameMaterial/tmp/{tempId}.glb"}`

### `POST /api/tags/{tag_code}/materials`

維持 Form。新增可選欄位 `temp_id`：

- 有 `temp_id`：把對應暫存檔搬進 Shared，副檔名跟著暫存檔（png 或 glb）。
- 沒有 `temp_id`：行為與現在相同（可選上傳圖，否則色塊 SVG）。

### `GET /api/unity/health`

比對 `X-Unity-Key` 與 `.env` 的 `UNITY_API_KEY`（`hmac.compare_digest`）。未設定 key 時一律 401。

## 錯誤碼

| 情況 | 狀態 |
|------|------|
| 沒登入打生成／入庫 | 401 |
| 物件名稱或生成描述空白 | 422 |
| 分類不存在 | 404 |
| 已有生成在跑 | 429 |
| 找不到 text2image／Trellis（沒開 MOCK） | 503 |
| 生成過程失敗 | 500 |
| `temp_id` 沒有檔、過期、或含 `/` `\\` `.` | 400 |
| Unity 沒帶或帶錯 key | 401 |

## 環境變數

寫進 `Final/backend/.env` 與 `.env.example`（example 不放真實 DB 密碼）。既有 `DB_*` 不動。

| 變數 | 說明 |
|------|------|
| `TEXT2IMAGE_ROOT` | text2image 專案目錄 |
| `TEXT2IMAGE_PYTHON` | 該專案 venv 的 python.exe |
| `TEXT2IMAGE_MOCK=1` | 不跑真 2D，寫占位 PNG |
| `TRELLIS_ROOT` | Trellis 原始碼目錄 |
| `TRELLIS_MODEL` | 權重路徑 |
| `ATTN_BACKEND` / `SPCONV_ALGO` | 預設 `xformers` / `native` |
| `TRELLIS_MOCK=1` | 不跑真 3D，寫占位 GLB |
| `UNITY_API_KEY` | Unity 探針識別碼 |

pytest `conftest` 強制 `TEXT2IMAGE_MOCK=1`、`TRELLIS_MOCK=1`。

## 啟動

本機（8000 若被擋則 8001）：

```powershell
cd Final\backend
uv run uvicorn backend.main:app --reload --port 8001
```

區網：

```powershell
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

## 前端

- 刪除該預覽流程。該流程是「模型還沒接、先用色塊當預覽」。
- `index.html` 載入與參考專案相同的 model-viewer 3.5.0。
- 生成中禁用送出、顯示「生成中…」。
- 3D 預覽與 3D 卡片：`camera-controls`、`auto-rotate`、`interaction-prompt="none"`、`shadow-intensity="1"`。

## 測試（pytest，一支檔一件事）

- `test_12_generate_auth.py`
- `test_13_generate_2d_validate.py`
- `test_14_generate_2d_mock.py`
- `test_15_generate_2d_accept.py`
- `test_16_generate_2d_bad_temp.py`
- `test_17_generate_3d_validate.py`
- `test_18_generate_3d_mock.py`
- `test_19_generate_3d_accept.py`
- `test_20_generate_busy.py`
- `test_21_unity_health.py`

實作後用瀏覽器走：登入 → 2D 生成預覽 → 加入 → 卡片有圖；3D 生成預覽可轉 → 加入 → 卡片可轉；Unity 探針對／錯 key。

## 完成條件（缺一不可）

1. 註解一句一事。沒有未要求的分支。
2. 不改 SQL 結構，入庫走 Shared + `file_path`。
3. 測試拆檔、由淺入深、MOCK、涵蓋上表錯誤碼。
4. 老師後台 001／002 可真生（沒開 MOCK 時）。
5. 003 只有 health 探針。
6. 3D 可拖曳旋轉，不是遊戲格子拖放。
