#!/bin/bash
set -e

# 現在のディレクトリをスクリプトのディレクトリに変更
cd "$(dirname "$0")/.."

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi

# 出力ディレクトリが存在することを確認
mkdir -p "output"

echo "統合テストを開始します..."

# Pythonの統合テストを実行
echo "Python統合テストを実行しています..."
cd ..
python -m unittest discover -s tests/integration

echo "統合テストが完了しました"
