#!/bin/bash
# ACE-Step Standalone 起動スクリプト

cd "$(dirname "$0")"

# 仮想環境を有効化
source .venv/bin/activate

# サーバー起動
echo "🎵 ACE-Step Standalone を起動します..."
echo "   URL: http://localhost:8888"
echo ""

python main.py
