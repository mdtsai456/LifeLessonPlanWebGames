# 005：記憶配對配置（Default／Customization／老師頁／Unity）

日期：2026-09-18  
狀態：已實作

## 目標

老師為一位學生配置記憶配對：先選主題，拖滿正確 4 格與錯誤 5 格，編輯開場 NPC，儲存後重新載入，設定仍在。沒自訂就退回開發者種子 Default。Unity 用 `X-Unity-Key` 讀組好的可玩 JSON。結束對白維持關卡配置。本文件只描述 `MemoryMatch`。

## 決策摘要

| 項目 | 決定 |
|------|------|
| 順序 | Default 種子 + GET → 學生 GET/PUT → 老師頁 → Unity GET |
| Default | 開發者寫 `storage/GameMaterialDefault/MemoryMatch.json`；老師不能改；沒有 PUT |
| Customization | `storage/GameMaterialCustomization/{老師}/{學生}/MemoryMatch.json` |
| 沒自訂 | 老師畫面與 Unity 都退回 Default |
| 格子 | `theme_1`…`theme_4` 必須來自選定 tag；`distractor_1`…`distractor_5` 必須不在該 tag；九格不重複 |
| 儲存 | 9 格必須填滿；`Start_NPC_Name` / `Start_Dialogues` 可空 |
| 開場 | 配置頁編輯；結束對話仍在關卡流程 |
| 畫面 | NPC 面板 + 格子 + 素材庫；不做預覽圖 |
| Unity | `GET /api/unity/students/{id}/games/MemoryMatch`；結束對白另打 workflow |
| 其他遊戲 | 配置頁維持「稍後提供」；material / Unity 回 400「此遊戲配置尚未提供」 |
| 資料庫 | 不改 schema；用既有 `GameMaterialDefault` / `GameMaterialCustomization` |

## 非目標

- 另外四款遊戲配置
- 老師編輯 Default
- 預覽截圖
- 遊玩碼 `/api/play?code=`
- 多份配置名稱、`configs` 陣列
- Unity GET 夾帶結束對白

## 老師存檔 JSON

```json
{
  "game": "MemoryMatch",
  "tag": "EDIBLE",
  "items": {
    "theme_1": "MAT003",
    "theme_2": "MAT004",
    "theme_3": "MAT005",
    "theme_4": "MAT006",
    "distractor_1": "MAT008",
    "distractor_2": "MAT009",
    "distractor_3": "MAT010",
    "distractor_4": "MAT011",
    "distractor_5": "MAT012"
  },
  "Start_NPC_Name": "阿姨",
  "Start_Dialogues": ["這裡有一些箱子,請你在空中按下方向鍵來敲開箱子,並找出四個可以吃的食物"]
}
```

## API

```http
GET  /api/games/MemoryMatch/materials/default
GET  /api/students/{id}/games/MemoryMatch/materials
PUT  /api/students/{id}/games/MemoryMatch/materials
GET  /api/games/MemoryMatch/library
GET  /api/unity/students/{id}/games/MemoryMatch
```

老師 API 要 Bearer。Unity 要 `X-Unity-Key`。Unity 成功時回 `game`、`studentName`、`theme`（code + name）、`slots`（各格 code / name / imageUrl）、`Start_NPC_Name`、`Start_Dialogues`。

## 使用流程

1. 老師選學生，打開遊戲配置 → 記憶配對。
2. 先選題目主題。正確格只能放該主題；錯誤格只能放其他主題。改主題會清掉不合規的格子。
3. 9 格滿才能按儲存。開場可空；畫面會先帶入 Default。
4. 「清除全部格子」只清 9 格，主題與開場留下。
5. Unity 讀格子與開場；關卡順序與結束對白打既有 workflow。
