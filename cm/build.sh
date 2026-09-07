#!/usr/bin/env bash
# 30秒CMを最初から書き出す。出力: cm/build/ep_marketing_cm_30s_1080p.mp4
set -euo pipefail
cd "$(dirname "$0")"
python3 narration.py   # ナレーション音声（Open JTalk）
python3 bgm.py         # BGM・効果音
python3 mix.py         # 音声ミックス（ダッキング込み）
python3 render.py      # 映像レンダリング＋H.264/AACでmux
