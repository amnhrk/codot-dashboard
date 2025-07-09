# Codot Dashboard

Codotの分析データを可視化するStreamlitベースのダッシュボードです。

## プロジェクト構造

```
codot_dashboard/
├── app.py                  # メインのStreamlitアプリケーション
├── pyproject.toml          # Poetry依存関係設定
├── .env.example           # 環境変数のサンプル
└── lib/
    ├── __init__.py        # ライブラリパッケージ初期化
    ├── etl.py             # データ抽出・変換・読み込み処理
    ├── kpi.py             # KPI（重要業績評価指標）計算
    └── ai_comment.py      # AI生成インサイト機能
```

## 機能

- 📊 **店舗KPI可視化**: 顧客数・客単価・生産性の月次推移
- 📈 **前年同期比較**: YoY分析で店舗パフォーマンス評価
- 🔮 **AI予測**: Prophet時系列モデルによる6か月先予測
- 🤖 **経営提案**: OpenAI GPT-4o-miniによる具体的アクションプラン
- ⚡ **自動ETL**: GitHub Actionsで毎日データ更新
- 🏪 **マルチ店舗**: 複数店舗の一元管理・比較分析

## セットアップ

### 1. 必要なAPIキー取得

#### OpenAI APIキー（必須）
1. [OpenAI Platform](https://platform.openai.com/)でアカウント作成
2. 「API Keys」セクションで新しいキーを生成
3. 課金設定：GPT-4o-mini使用で約$5-20/月
4. APIキーをコピー（sk-で始まる文字列）

#### 環境変数設定
```bash
# 環境変数ファイルを作成
cp .env.example .env

# OpenAI APIキーを設定（必須）
echo "OPENAI_API_KEY=sk-your-actual-api-key-here" > .env
```

**注意**: APIキーは秘密情報です。`.env`ファイルをGitにコミットしないでください。

### 2. 依存関係のインストール

#### Poetryを使用する場合:
```bash
# Poetryをインストール（まだの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係をインストール
poetry install

# 仮想環境をアクティベート
poetry shell
```

#### pipを使用する場合:
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係をインストール
pip install pandas plotly streamlit prophet openai sqlite-utils
```

### 3. アプリケーションの実行

```bash
# Streamlitアプリを起動
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセスしてダッシュボードを表示します。

### 4. GitHub Actions設定（本番運用時）

自動ETLを有効化するには、GitHubリポジトリでシークレット設定が必要です：

1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. New repository secretで以下を追加：
   - `OPENAI_API_KEY`: OpenAI APIキー
   - `CODOT_API_KEY`: Codot APIキー（将来的に実装時）

これにより毎日7:00 JSTに自動でデータ更新が実行されます。

## 依存関係

- **pandas**: データ操作と分析
- **plotly**: インタラクティブな可視化
- **streamlit**: Webアプリケーションフレームワーク
- **prophet**: 時系列予測
- **openai**: AI生成インサイト
- **sqlite-utils**: SQLiteデータベース操作

## 使用方法

### ダッシュボード操作
1. **ファイルアップロード**: CodotのExcelファイルをドラッグ&ドロップ
2. **店舗選択**: 分析対象店舗をプルダウンから選択
3. **期間設定**: 表示月数をスライダーで調整（1-12ヶ月）

### 4つの分析タブ
1. **顧客数**: 月次顧客数推移 + 前年同期比較
2. **客単価**: 平均客単価トレンド + YoY分析
3. **生産性**: 売上/労働時間の効率指標
4. **AIレポート**: Prophet予測 + OpenAI経営提案

## カスタマイズ

- `lib/etl.py`: データソースの設定変更
- `lib/kpi.py`: KPI計算ロジックの調整
- `lib/ai_comment.py`: AI分析プロンプトのカスタマイズ
- `app.py`: UIレイアウトと新機能の追加

## ライセンス

MIT License 