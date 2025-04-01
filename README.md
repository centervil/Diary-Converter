# Diary Converter

開発日記をZenn記事に変換するためのツールです。Gemini APIを使用して、開発日記の内容を自動的にZenn記事のフォーマットに変換します。

## 機能

- 開発日記からZenn記事への自動変換
- カスタマイズ可能なテンプレート
- 開発サイクル記事との連携
- デバッグモードによる詳細なログ出力

## インストール

### 依存関係

- Python 3.10以上
- Gemini APIキー

### セットアップ

1. リポジトリをクローン:
```bash
git clone https://github.com/centervil/Diary-Converter.git
cd Diary-Converter
```

2. 依存パッケージをインストール:
```bash
pip install -r requirements.txt
```

3. 環境変数の設定:
```bash
export GOOGLE_API_KEY="your-api-key"
```

## 使用方法

### コマンドライン

```bash
python -m diary_converter.diary_converter \
  input.md \
  output.md \
  --model "gemini-2.0-flash-001" \
  --template "templates/zenn_template.md" \
  --debug
```

### GitHub Actions

```yaml
- name: Run diary-converter
  uses: centervil/Diary-Converter@main
  with:
    source_file: path/to/source.md
    destination_file: path/to/output.md
    api_key: ${{ secrets.GOOGLE_API_KEY }}
    model: gemini-2.0-flash-001
    template: path/to/template.md
    debug: 'true'
```

## プロジェクト構造

```
Diary-Converter/
├── .github/
│   └── workflows/          # GitHub Actionsのワークフローファイル
├── docs/
│   ├── project-logs/      # 開発日記
│   └── api/              # APIドキュメント
├── src/
│   └── diary_converter/  # メインのPythonコード
├── tests/
│   ├── fixtures/         # テスト用のフィクスチャ（入力ファイルやテンプレートなど）
│   ├── integration/      # 統合テスト
│   ├── output/           # テスト出力ディレクトリ
│   ├── scripts/          # テスト実行スクリプト
│   └── unit/             # ユニットテスト
├── templates/            # テンプレートファイル
├── input/                # 入力ファイル用ディレクトリ
├── output/               # 出力ファイル用ディレクトリ
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
├── README.md
└── LICENSE
```

## テスト

すべてのテストはDocker環境で実行されます。以下のコマンドでテストを実行できます：

### Docker環境でのユニットテスト

```bash
cd Diary-Converter
tests/scripts/run_docker_unit_tests.sh
```

### Docker環境での統合テスト

```bash
cd Diary-Converter
tests/scripts/run_docker_integration_tests.sh
```

### Docker環境での機能テスト

```bash
cd Diary-Converter
tests/scripts/run_docker_tests.sh
```

### すべてのテストを実行

```bash
cd Diary-Converter
tests/scripts/run_all_tests.sh
```

注意: すべてのテストを実行するには、Docker環境が必要です。また、`GOOGLE_API_KEY`環境変数が設定されている必要があります。

### CI/CDパイプライン

GitHub Actionsを使用して、プッシュやプルリクエスト時に自動的にテストが実行されます。
詳細は `.github/workflows/test.yml` を参照してください。

## ライセンス

MIT License
