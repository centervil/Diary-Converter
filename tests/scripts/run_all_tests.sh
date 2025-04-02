#!/bin/bash
set -e

echo "Docker環境で全てのテストを実行します..."

# ユニットテストを実行
echo ""
echo "=== Docker環境でユニットテストを実行します ==="
bash run_docker_unit_tests.sh
echo "=== Docker環境でユニットテストが完了しました ==="
echo ""

# エンドツーエンドテスト (旧 統合テスト) を実行
echo "=== Docker環境でエンドツーエンドテストを実行します ==="
echo "イメージをビルドしています (キャッシュ利用)..."
# ビルドはユニットテストで実行済みのはずだが念のため
docker-compose build diary-converter

echo "E2Eテストを実行しています..."
# docker-compose run を使ってコンテナ内で unittest を実行
docker-compose run --rm diary-converter python -m unittest discover -s tests/integration

echo "=== Docker環境でエンドツーエンドテストが完了しました ==="
echo ""

echo "すべてのテストが正常に完了しました！"
