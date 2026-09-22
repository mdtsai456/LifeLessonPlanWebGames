# 素材類型文案：Image / Model

日期：2026-09-17  
狀態：確認規格後才實作。

## 目標

老師後台「選擇素材類型」與後續畫面，把使用者看得到的 `2D cube` / `3D model` 改成更短的 **Image** / **Model**。行為不變。

## 決策摘要

| 項目 | 決定 |
|------|------|
| 範圍 | 方案 C：所有使用者看得到的舊文案都改 |
| 作法 | 方案 1：直接改 `app.js` 字串，不抽常數、不加 Playwright |
| 測試 | 先跑新的前端文案 pytest（B），再跑完整後端測試（A） |
| API | 不改。函式名、`kind`、後端檔案都不動 |
| 2D 卡片 | 本來沒有類型標籤，不加 `Image` |

## 非目標

- 改生成流程、API、資料庫、CSS
- 給 2D 卡片加上 `Image` 標籤
- 改 `cube_generate.py` 等後端註解
- 新裝前端測試框架

## 畫面文案

只改 `Final/frontend/js/app.js`。

| 位置 | 現在 | 改成 |
|------|------|------|
| 類型按鈕 | `2D cube` | `Image` |
| 類型按鈕 | `3D model` | `Model` |
| 表單標題／對話框名稱 | `新增 2D cube` | `新增 Image` |
| 表單標題／對話框名稱 | `新增 3D model` | `新增 Model` |
| 3D 卡片灰色標籤 | `3D model` | `Model` |
| 檔頭註解 | 先選 2D cube / 3D model | 先選 Image / Model |

## 測試

沿用 pytest + TestClient，讀 `/js/app.js`。比對**畫面字串**，不要只搜 `Image` / `Model`（檔裡還有 `isModel`、`model-viewer` 等）。拆兩支檔、由淺入深：

1. `Final/backend/tests/test_22_frontend_labels_new.py`  
   確認有 `text: "Image"`、`text: "Model"`、`新增 Image`、`新增 Model`。
2. `Final/backend/tests/test_23_frontend_labels_old.py`  
   確認沒有 `2D cube`、`3D model`。

驗證順序：先跑 test_22 與 test_23，再跑完整後端測試。使用專案 venv。

## 程式風格

不加未要求的抽象。註解使用與畫面相同的用語。
