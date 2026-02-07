#!/bin/bash
# ACE-Step Standalone 起動スクリプト

cd "$(dirname "$0")"

# 仮想環境を有効化
if [ -f "./.venv/bin/activate" ]; then
	source ./.venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
	source ../.venv/bin/activate
fi

# サーバー起動
echo "🎵 ACE-Step Standalone を起動します..."
echo "   URL: http://localhost:8888"
echo ""

python3 main.py
