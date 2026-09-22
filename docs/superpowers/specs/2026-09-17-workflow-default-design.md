# 004：預設關卡 GET /api/workflow/default

日期：2026-09-17  
狀態：已實作

## 目標

老師登入後讀得到全站預設關卡順序。沒有學生 id。沒有 PUT。不動前端。

## 決策摘要

| 項目 | 決定 |
|------|------|
| URL | `GET /api/workflow/default` |
| 權限 | 與素材庫相同，要 Bearer；沒登入 401 |
| 檔案 | `Final/backend/storage/GameWorkflowDefault/workflow.json` |
| 資料庫 | 既有 `GameWorkflowDefault.json_path`；不改 schema |
| 沒列 | 退回字串 `GameWorkflowDefault/workflow.json` |
| 檔不在 | 404 |
| JSON 壞掉 | 500 |
| 回傳 | 檔案內容本身 `{ "games": [ { "game", "order" } ] }` |
| 測試 | pytest 拆 `test_29`～`test_34`，由淺入深 |

## 非目標

- `GameWorkflowCustomization`
- 學生 API
- 前端
- 把 `storage/` 掛成 StaticFiles
- Unity 讀 workflow
- import Jack / Jenny 程式

## 使用流程

```http
GET /api/workflow/default
Authorization: Bearer <token>
```

成功 200，body 為五款遊戲的 `game` + `order`。老師之後幫學生自訂關卡，才會另做學生 workflow API。
