#!/bin/bash
set -e

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  # テスト実行時はAPIキーがなくても続行できるようにコメントアウト
  # exit 1
fi

# 引数が 'bash', 'python', 'pytest', 'unittest' などで始まる場合は、それをコマンドとして実行
# これにより、docker-compose run でカスタムコマンドを実行できるようになる
if [[ "$1" == "bash" || "$1" == "python" || "$1" == "pytest" || "$1" == "unittest" ]]; then
  echo "Executing command: $@"
  exec "$@"
fi

# --- 通常の diary_converter.py 実行ロジック ---

# APIキーが設定されているか再度確認（通常の実行時のみ必須）
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi


# 引数が正しく渡されているか確認
if [ "$#" -lt 2 ]; then
  echo "使用方法: $0 <入力ファイル> <出力ファイル> [--model モデル名] [--debug]"
  echo "例: $0 input/2025-03-10-Claude-Cursor連携開発.md output/2025-03-10-claude-cursor.md"
  exit 1
fi

# 入力ファイルと出力ファイルのパスを設定
INPUT_FILE="$1"
OUTPUT_FILE="$2"
shift 2

# Pythonパスを設定
export PYTHONPATH=/app/src:$PYTHONPATH

# モジュールの存在を確認 (デバッグ用、本番では不要かも)
echo "Pythonモジュールの確認:"
python -c "import sys; print(sys.path)"
python -c "import os; print(os.listdir('/app/src'))"

# 残りの引数をそのまま渡して diary_converter を実行
echo "Executing diary_converter.py with input: $INPUT_FILE, output: $OUTPUT_FILE, args: $@"
cd /app
exec python -m src.diary_converter.diary_converter "$INPUT_FILE" "$OUTPUT_FILE" "$@"
