FROM python:3.10-slim

WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ /app/src/
COPY tests/ /app/tests/
COPY templates/ /app/templates/

# 環境変数の設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 作業ディレクトリの設定
WORKDIR /app

# コマンドの設定
CMD ["python3"] 