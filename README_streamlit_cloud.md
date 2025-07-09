# 📸 Codotダッシュボード - Streamlit Cloud デプロイガイド

キャラット店舗ダッシュボードシステムをStreamlit Cloudで簡単にデプロイ！

## 🚀 クイックスタート

### 1. **GitHubにフォーク/クローン**
このリポジトリをGitHubアカウントにフォークしてください。

### 2. **Streamlit Cloudにアクセス**
1. [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
2. GitHubアカウントでサインイン
3. 「Create an app」をクリック

### 3. **アプリ設定**
- **GitHub repo**: あなたのフォークしたリポジトリを選択
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL**: 任意のURL名を入力

### 4. **🔑 APIキー設定（重要）**
デプロイ前に「Advanced settings」→「Secrets」で以下を設定：

```toml
OPENAI_API_KEY = "sk-proj-YOUR-ACTUAL-API-KEY-HERE"
```

### 5. **🎉 デプロイ実行**
「Deploy!」ボタンをクリックして完了！

## 📊 ダッシュボード機能

### ✨ **主要機能**
- 📈 **KPI可視化**: 顧客数・客単価・生産性トレンド
- 🔮 **AI予測**: Prophet時系列モデルによる6ヶ月先予測
- 🤖 **AIレポート**: GPT-4o-miniによる改善提案
- 📁 **データアップロード**: Excel複数ファイル対応

### 📱 **レスポンシブUI**
- デスクトップ・タブレット・スマートフォン対応
- インタラクティブなPlotlyグラフ
- 直感的な日本語インターフェース

## 🔧 カスタマイズ

### **店舗データ追加**
Excelファイルをアップロードするか、SQLiteデータベースを直接編集

### **AI設定変更**
`lib/ai_comment.py`でGPTモデルやプロンプトをカスタマイズ可能

### **デザイン変更**
`.streamlit/config.toml`でテーマカラーを変更

## 🆘 トラブルシューティング

### **よくある問題**

1. **「No module named 'lib'」エラー**
   → Streamlit Cloudが依存関係をインストール中。数分待ってリロード

2. **「OpenAI API key not found」**
   → Secrets設定でAPIキーが正しく設定されているか確認

3. **グラフが表示されない**
   → ブラウザをリロードするか、別ブラウザで試行

### **ログ確認**
Streamlit Cloudの管理画面「Logs」タブでエラーメッセージを確認

## 📚 システム構成

```
codot_dashboard/
├── app.py                 # メインアプリケーション
├── requirements.txt       # Python依存関係
├── .streamlit/
│   ├── config.toml       # Streamlit設定
│   └── secrets.toml      # APIキー等（.gitignoreで除外）
└── lib/
    ├── etl.py            # データ変換処理
    ├── kpi.py            # KPI分析・可視化
    └── ai_comment.py     # AI分析レポート
```

## 🔄 更新・メンテナンス

### **コード更新**
GitHubにプッシュすると自動でStreamlit Cloudに反映

### **APIキー更新**
Streamlit Cloud管理画面のSecretsで変更可能

### **データバックアップ**
重要データは定期的にExcelエクスポートを推奨

## 🎯 本番運用Tips

1. **独自ドメイン**: Streamlit Cloud Proで独自ドメイン設定可能
2. **アクセス制限**: パスワード認証追加可能
3. **パフォーマンス**: 大量データは事前処理・キャッシュ活用
4. **監視**: Streamlit Cloud管理画面でアプリ状態監視

---

## 🤝 サポート

質問・バグ報告・機能要望は[Issues](../../issues)からお気軽にどうぞ！

**Happy Analytics! 📊✨** 