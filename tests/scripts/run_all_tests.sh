#!/bin/bash
set -e

# 現在のディレクトリをスクリプトのディレクトリに変更
cd "$(dirname "$0")"

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi

echo "すべてのテストを実行します..."

# ユニットテストを実行
echo "=== ユニットテストを実行します ==="
./run_unit_tests.sh
echo "=== ユニットテストが完了しました ==="
echo

# 統合テストを実行
echo "=== 統合テストを実行します ==="
./run_integration_tests.sh
echo "=== 統合テストが完了しました ==="
echo

# Dockerテストを実行
echo "=== Dockerテストを実行します ==="
./run_docker_tests.sh
echo "=== Dockerテストが完了しました ==="
echo

echo "すべてのテストが正常に完了しました！"
