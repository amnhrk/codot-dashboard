# 🚀 Codotダッシュボード 本番環境セットアップガイド

## 📋 本番環境の選択肢

### 1. **ローカル本番環境**（推奨：社内利用）
```bash
# Poetry環境セットアップ
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# プロジェクトセットアップ
cd codot_dashboard
poetry install

# 環境変数設定
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 本番起動
poetry run streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 2. **Docker本番環境**（推奨：スケーラブル）
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install --no-dev
ENV OPENAI_API_KEY=""

EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### 3. **クラウドデプロイ**

#### Heroku
```bash
# heroku.yml
build:
  docker:
    web: Dockerfile

# アプリ作成・デプロイ
heroku create codot-dashboard
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

#### Streamlit Cloud（最も簡単）
- GitHub連携で自動デプロイ
- 環境変数はWebUI で設定
- 無料プランあり

#### AWS/GCP/Azure
- EC2/Compute Engine/VM でDocker実行
- ロードバランサー + 複数インスタンス
- データベースは RDS/CloudSQL 等

## 🔐 セキュリティ設定

### 環境変数管理
```bash
# 本番用 .env
OPENAI_API_KEY=sk-proj-...
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### アクセス制御
```python
# app.py に追加
import streamlit_authenticator as stauth

# Basic認証
def check_password():
    def password_entered():
        if st.session_state["password"] == "your_secure_password":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("パスワード", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワード", type="password", on_change=password_entered, key="password")
        st.error("パスワードが間違っています")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

## 🗄️ データベース本番化

### SQLite → PostgreSQL
```python
# config.py
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///codot.db')

# requirements に追加
# psycopg2-binary==2.9.7
```

### データバックアップ
```bash
# 日次バックアップスクリプト
#!/bin/bash
DATE=$(date +%Y%m%d)
cp codot.db backups/codot_${DATE}.db
```

## 📊 モニタリング

### ログ設定
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### ヘルスチェック
```python
# health_check.py
import requests
import sys

try:
    response = requests.get('http://localhost:8501/_stcore/health')
    if response.status_code == 200:
        print("✅ アプリ正常")
    else:
        print("❌ アプリエラー")
        sys.exit(1)
except:
    print("❌ 接続エラー")
    sys.exit(1)
```

## 🔄 自動デプロイ（GitHub Actions）

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "codot-dashboard"
          heroku_email: "your-email@example.com"
```

## ⚡ パフォーマンス最適化

### キャッシュ設定
```python
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def load_kpi_data(store_id, months):
    return get_store_data(store_id, months)
```

### 並列処理
```python
from concurrent.futures import ThreadPoolExecutor

def generate_all_reports():
    stores = get_store_list()
    with ThreadPoolExecutor(max_workers=4) as executor:
        reports = list(executor.map(generate_report, stores))
    return reports
```

## 📈 本番運用チェックリスト

- [ ] 環境変数の安全な管理
- [ ] アクセス制御の実装
- [ ] データベースバックアップ
- [ ] ログ・モニタリング設定
- [ ] エラーハンドリング
- [ ] パフォーマンス最適化
- [ ] 自動デプロイ設定
- [ ] ドキュメント整備 