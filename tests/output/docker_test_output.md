```markdown
---
title: "diary_converter.py 動作確認のためのDocker環境構築"
emoji: "🐳"
type: "tech"
topics: ['Docker', 'Python', 'Zenn']
published: false
---

:::message
この記事はgemini-2.0-flash-001によって自動生成されています。

:::

:::message
この記事はgemini-2.0-flash-001によって自動生成されています。
私の毎日の開発サイクルについては、[開発サイクルの紹介記事へのリンク]をご覧ください。
:::

# diary_converter.py 動作確認のためのDocker環境構築

## はじめに

昨日はCline設定の最適化を行いました。今日は、diary_converter.pyの動作確認を行うためのDocker環境を構築します。

## 背景と目的

diary_converter.pyは、開発日記をZenn公開用の記事に変換するためのツールです。このツールはGoogle Gemini APIを使用しており、動作確認のためには安定した実行環境が不可欠です。そこで、Docker環境を構築し、再現性の高いテスト環境を整備することを目的とします。

## 検討内容

### 課題の整理

1.  **Docker環境の構築**: diary_converter.pyを実行するための環境が必要です。
2.  **ボリュームマウントの設定**: 入力ファイルと出力ファイルのパスを適切に設定する必要があります。

### 解決アプローチ

1.  **Dockerfileの作成**: Python 3.9をベースイメージとして使用し、必要なパッケージをインストールするDockerfileを作成します。
2.  **docker-compose.ymlの設定**: ボリュームマウントを設定し、入力ディレクトリと出力ディレクトリを指定します。

## 実装内容

まず、Dockerfileを作成しました。以下にDockerfileの内容を示します。

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "diary_converter.py"]
```

次に、docker-compose.ymlを作成しました。これにより、ボリュームマウントを簡単に設定できます。

```yaml
version: "3.9"
services:
  app:
    build: .
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

これらのファイルを作成後、`docker-compose up --build` コマンドを実行し、Docker環境を構築しました。

## 技術的なポイント

Dockerfileでは、`pip install --no-cache-dir -r requirements.txt` を使用して、キャッシュを使用せずにパッケージをインストールしています。これにより、イメージサイズを削減し、ビルド時間を短縮できます。

docker-compose.ymlでは、`volumes` を使用して、ホストマシンの `./input` ディレクトリをコンテナの `/app/input` ディレクトリに、`./output` ディレクトリを `/app/output` ディレクトリにマウントしています。これにより、ホストマシン上で入力ファイルを作成し、コンテナ内で処理された出力ファイルをホストマシン上で確認できます。

## 所感

Docker環境の構築は、diary_converter.pyの動作確認を効率化するために非常に重要です。今回の作業を通じて、Dockerの基本的な使い方を再確認できました。特に、ボリュームマウントの設定は、開発効率を向上させる上で欠かせない要素だと感じました。環境構築自体はスムーズに進みましたが、Gemini APIの認証情報を環境変数として渡す部分で少し手間取りました。今後は、より複雑な設定にも対応できるよう、Dockerに関する知識を深めていきたいです。

## 今後の課題

1.  テストケースの作成と実行
2.  エラーハンドリングの改善
3.  他のLLM APIへの対応検討

## まとめ

diary_converter.pyの動作確認のためのDocker環境を構築しました。Dockerfileとdocker-compose.ymlを作成し、必要なボリュームマウントを設定しました。これにより、開発日記をZenn公開用の記事に変換する作業が効率化されます。今後は、テストケースの作成やエラーハンドリングの改善に取り組み、より実用的なツールへと進化させていきたいと考えています。
```