---
title: 🥚 Egg Timer Web App
emoji: "🥚"
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
pinned: false
---

A simple web app that calculates perfect egg boiling time based on:
- Number of eggs
- Desired doneness
- Heat conditions

## Features
- Clean UI
- Adjustable timing formula
- Confetti celebration when done 🎉

## Tech Stack
- Python / Flask (or JS)
- HTML/CSS

## Demo
https://huggingface.co/spaces/kenlolhku/egg-timer

# 蛋蛋計時小幫手 (Hugging Face Space)

一個以廣東話引導的煮蛋小工具，會一步一步帶你完成：

1. 煲滾水  
2. 轉細火  
3. 放蛋  
4. 開始按熟度與蛋數計時  
5. 完成提示（建議過冰水）

## 功能

- 熟度選項：`流心`、`軟心`、`全熟`（必選）
- 蛋數調整：1-12 隻
- 參數一改就即時更新建議時間（未選熟度會顯示 `--:--`）
- 自動按蛋數微調烹調時間（每多一隻蛋加少量秒數）
- 友善廣東話步驟提示 + 即時倒數
- 大字體時間顯示，倒數更清楚

## 本機執行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

瀏覽器打開本機顯示嘅網址（通常係 `http://127.0.0.1:7860`）。

## Hugging Face Space 部署

1. 在 Hugging Face 建立新 Space（選 `Gradio`）。
2. 將以下檔案推上 Space repo：
   - `app.py`
   - `egg_timing.py`
   - `requirements.txt`
   - `README.md`
3. Space 會自動安裝依賴並啟動 App。

## 時間設定

預設基準（可在 `egg_timing.py` 調整）：

- `Jammy`: 7:00
- `Soft boiled`: 6:30
- `Hard boiled`: 10:30

每多一隻蛋（第一隻以外）會加少量秒數，模擬放蛋後水溫回落。
