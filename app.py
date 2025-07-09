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

# --- Controls ----------------------------------------------
store = st.selectbox("店舗を選択", kpi.get_store_list())
months = st.slider("表示月数", 1, 12, 3)

tabs = st.tabs(["顧客数", "客単価", "生産性", "AI レポート"])

with tabs[0]:
    st.plotly_chart(kpi.plot_customer_trend(store, months), use_container_width=True)
with tabs[1]:
    st.plotly_chart(kpi.plot_spend_trend(store, months), use_container_width=True)
with tabs[2]:
    st.plotly_chart(kpi.plot_productivity(store, months), use_container_width=True)
with tabs[3]:
    st.markdown(ai_comment.generate(store, months), unsafe_allow_html=True) 