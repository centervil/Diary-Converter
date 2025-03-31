#!/bin/bash
set -e

# 現在のディレクトリをスクリプトのディレクトリに変更
cd "$(dirname "$0")/.."

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi

# テスト用の入力ファイルと出力ファイルのパスを設定
INPUT_FILE="fixtures/test_input.md"
OUTPUT_FILE="output/test_output.md"
TEMPLATE_FILE="fixtures/test_template.md"

echo "ユニットテストを開始します..."
echo "入力ファイル: $INPUT_FILE"
echo "出力ファイル: $OUTPUT_FILE"
echo "テンプレートファイル: $TEMPLATE_FILE"

# 出力ディレクトリが存在することを確認
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Pythonのユニットテストを実行
echo "Pythonユニットテストを実行しています..."
cd ..
python -m unittest discover -s tests/unit

echo "ユニットテストが完了しました"
