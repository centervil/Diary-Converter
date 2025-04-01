#!/bin/bash
set -e

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")/../.."

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi

echo "Docker環境でユニットテストを開始します..."

# イメージをビルド
echo "イメージをビルドしています..."
docker-compose build diary-converter

# コンテナを実行してユニットテストを実行
echo "ユニットテストを実行しています (ダミーAPIキーを使用)..."
# ユニットテストでは実際のAPIキーを使わないようにダミーキーを設定
export GOOGLE_API_KEY="DUMMY_API_KEY_FOR_UNIT_TEST" 
docker-compose run --rm -e GOOGLE_API_KEY=$GOOGLE_API_KEY diary-converter bash -c "cd /app && python -m unittest discover -s tests/unit"
# 元の環境変数を汚染しないようにunsetしておく (シェルスクリプト内なので必須ではないが念のため)
unset GOOGLE_API_KEY 

echo "Docker環境でのユニットテストが完了しました"
