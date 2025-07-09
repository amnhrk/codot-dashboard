"""
Codot Dashboard - Main Application
"""

import os
import streamlit as st
from lib import etl, kpi, ai_comment

# Streamlit Cloudのsecrets設定（本番環境用）
if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
    os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']

st.set_page_config(page_title="キャラット Codot ダッシュボード", layout="wide")

st.title("📸 キャラット店舗ダッシュボード")

# 🔧 デバッグ: サンプルデータ自動生成
if 'sample_data_loaded' not in st.session_state:
    try:
        with st.spinner('サンプルデータを準備中...'):
            result = etl.setup_sample_database()
            st.success(f"✅ {result}")
            st.session_state.sample_data_loaded = True
    except Exception as e:
        st.error(f"❌ サンプルデータ生成エラー: {str(e)}")

# 🔍 デバッグ情報表示
with st.expander("🔧 デバッグ情報", expanded=False):
    try:
        stores = kpi.get_store_list()
        st.write(f"**利用可能店舗**: {stores}")
        st.write(f"**店舗数**: {len(stores)}")
        
        if stores:
            st.write("**データベース接続**: ✅ 正常")
            # テスト用に最初の店舗の基本データを表示
            test_store = stores[0]
            st.write(f"**テスト店舗**: {test_store}")
        else:
            st.write("**データベース接続**: ❌ 店舗データなし")
            
    except Exception as e:
        st.error(f"**デバッグエラー**: {str(e)}")

# --- Upload -------------------------------------------------
uploaded = st.file_uploader(
    "Codot の Excel をまとめてドラッグ＆ドロップ",
    type=["xlsx"],
    accept_multiple_files=True
)
if uploaded:
    st.info("取り込み開始…")
    summary = etl.load_excels(uploaded)
    st.success(f"完了: {summary}")
    # アップロード後にページをリロードして新しいデータを反映
    st.rerun()

# --- Controls ----------------------------------------------
try:
    stores = kpi.get_store_list()
    if stores:
        store = st.selectbox("店舗を選択", stores)
        months = st.slider("表示月数", 1, 12, 3)

        tabs = st.tabs(["顧客数", "客単価", "生産性", "AI レポート"])

        with tabs[0]:
            try:
                fig = kpi.plot_customer_trend(store, months)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("顧客数データがありません")
            except Exception as e:
                st.error(f"顧客数グラフエラー: {str(e)}")

        with tabs[1]:
            try:
                fig = kpi.plot_spend_trend(store, months)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("客単価データがありません")
            except Exception as e:
                st.error(f"客単価グラフエラー: {str(e)}")

        with tabs[2]:
            try:
                fig = kpi.plot_productivity(store, months)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("生産性データがありません")
            except Exception as e:
                st.error(f"生産性グラフエラー: {str(e)}")

        with tabs[3]:
            try:
                with st.spinner('AIレポート生成中...'):
                    report = ai_comment.generate(store, months)
                    st.markdown(report, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AIレポートエラー: {str(e)}")
    else:
        st.error("❌ 店舗データが見つかりません。")
        st.info("💡 上記のファイルアップロード機能を使用してExcelファイルをアップロードするか、システム管理者にお問い合わせください。")

except Exception as e:
    st.error(f"アプリケーションエラー: {str(e)}")
    st.info("ページをリロードしてお試しください。") 