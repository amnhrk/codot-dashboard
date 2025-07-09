#!/bin/bash

# 🚀 Codotダッシュボード 本番環境起動スクリプト

set -e

echo "🔧 Codotダッシュボード本番環境を開始します..."

# 環境変数チェック
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ エラー: OPENAI_API_KEY環境変数が設定されていません"
    echo "   以下のコマンドで設定してください:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# Poetry インストールチェック
if ! command -v poetry &> /dev/null; then
    echo "📦 Poetryをインストールしています..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# 依存関係のインストール
echo "📦 依存関係をインストールしています..."
poetry install --no-dev

# データベース初期化
echo "🗄️ データベースを初期化しています..."
poetry run python -c "
from lib.etl import setup_sample_database
from lib.kpi import get_store_list

print('📊 サンプルデータベースを作成中...')
setup_sample_database()

stores = get_store_list()
print(f'✅ {len(stores)}店舗のデータが準備されました')
"

# バックアップディレクトリ作成
mkdir -p backups
mkdir -p data

echo "🎉 準備完了！ダッシュボードを起動しています..."
echo "🌐 ブラウザで http://localhost:8501 にアクセスしてください"
echo "⏹️  停止するには Ctrl+C を押してください"

# Streamlit起動
poetry run streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false 