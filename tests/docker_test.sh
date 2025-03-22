#!/bin/bash
set -e

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")/.."

# APIキーが設定されているか確認
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "エラー: GOOGLE_API_KEY 環境変数が設定されていません"
  exit 1
fi

# 出力ディレクトリを作成
mkdir -p tests/output

echo "Docker環境でのテストを開始します..."

# イメージをビルド
echo "イメージをビルドしています..."
docker-compose build

# テスト用の入力ファイルと出力ファイルのパスを設定
INPUT_FILE="/app/tests/test_input.md"
OUTPUT_FILE="/app/tests/output/docker_test_output.md"
TEMPLATE_FILE="/app/tests/test_template.md"

echo "入力ファイル: $INPUT_FILE"
echo "出力ファイル: $OUTPUT_FILE"
echo "テンプレートファイル: $TEMPLATE_FILE"

# コンテナを実行
echo "コンテナを実行しています..."
docker-compose run --rm diary-converter \
  python3 -c "import sys; sys.path.append('/app/src'); from diary_converter.diary_converter import DiaryConverter; DiaryConverter(model='gemini-2.0-flash-001', template_path='$TEMPLATE_FILE', debug=True).convert('$INPUT_FILE', '$OUTPUT_FILE')"

# 出力ファイルが生成されたか確認
if [ -f "tests/output/docker_test_output.md" ]; then
  echo "テスト成功: 出力ファイルが生成されました"
  echo "出力ファイルの内容:"
  echo "-----------------------------------"
  cat "tests/output/docker_test_output.md"
  echo "-----------------------------------"
else
  echo "テスト失敗: 出力ファイルが生成されませんでした"
  exit 1
fi

echo "Docker環境でのテストが完了しました" 