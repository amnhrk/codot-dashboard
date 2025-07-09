FROM python:3.11-slim

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetryのインストール
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 作業ディレクトリの設定
WORKDIR /app

# Poetry設定ファイルをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係のインストール（開発依存関係は除く）
RUN poetry config virtualenvs.create false && poetry install --no-dev

# アプリケーションファイルをコピー
COPY . .

# ポート8501を公開
EXPOSE 8501

# 環境変数
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlitアプリの起動
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"] 