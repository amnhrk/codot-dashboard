"""
AI Comment Module
Generate AI-powered store analytics reports with Prophet forecasting
"""

import os
import logging
import sqlite3
import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import OpenAI

logger = logging.getLogger(__name__)


def _fetch_df(sql: str, params: tuple = (), db_path: str = "codot.db") -> pd.DataFrame:
    """
    Internal helper function to fetch data from SQLite database
    
    Args:
        sql: SQL query string
        params: Query parameters tuple
        db_path: Path to SQLite database
        
    Returns:
        DataFrame with query results
    """
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def _get_kpi_aggregates(store_id: str, months: int = 3, db_path: str = "codot.db") -> Dict[str, Any]:
    """
    Get KPI aggregates for the specified period
    
    Args:
        store_id: Store identifier
        months: Number of months to analyze
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with KPI metrics
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    prev_month_start = start_date - timedelta(days=30)
    prev_year_start = start_date - timedelta(days=365)
    prev_year_end = end_date - timedelta(days=365)
    
    # Current period
    sql_current = """
    SELECT 
        SUM(c.customer_count) as total_customers,
        AVG(s.average_spend) as avg_spend,
        SUM(sales.sales_amount) / SUM(l.work_hours) as productivity
    FROM customers_daily c
    LEFT JOIN spend_daily s ON c.sales_date = s.sales_date AND c.store_id = s.store_id
    LEFT JOIN sales_daily sales ON c.sales_date = sales.sales_date AND c.store_id = sales.store_id
    LEFT JOIN labor_daily l ON c.sales_date = l.sales_date AND c.store_id = l.store_id
    WHERE c.store_id = ? AND c.sales_date >= ? AND c.sales_date <= ?
    """
    
    current_data = _fetch_df(sql_current, (store_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), db_path)
    
    # Previous month
    prev_month_data = _fetch_df(sql_current, (store_id, prev_month_start.strftime('%Y-%m-%d'), start_date.strftime('%Y-%m-%d')), db_path)
    
    # Previous year same period
    prev_year_data = _fetch_df(sql_current, (store_id, prev_year_start.strftime('%Y-%m-%d'), prev_year_end.strftime('%Y-%m-%d')), db_path)
    
    def safe_get_value(data, column):
        """Safely get value from DataFrame with None check"""
        if data.empty or column not in data.columns:
            return 0
        value = data[column].iloc[0]
        return value if value is not None and not pd.isna(value) else 0
    
    result = {
        'current': {
            'customers': safe_get_value(current_data, 'total_customers'),
            'avg_spend': safe_get_value(current_data, 'avg_spend'),
            'productivity': safe_get_value(current_data, 'productivity')
        },
        'prev_month': {
            'customers': safe_get_value(prev_month_data, 'total_customers'),
            'avg_spend': safe_get_value(prev_month_data, 'avg_spend'),
            'productivity': safe_get_value(prev_month_data, 'productivity')
        },
        'prev_year': {
            'customers': safe_get_value(prev_year_data, 'total_customers'),
            'avg_spend': safe_get_value(prev_year_data, 'avg_spend'),
            'productivity': safe_get_value(prev_year_data, 'productivity')
        }
    }
    
    return result


def _get_daily_data_for_forecast(store_id: str, db_path: str = "codot.db") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get daily data for Prophet forecasting
    
    Args:
        store_id: Store identifier
        db_path: Path to SQLite database
        
    Returns:
        Tuple of (customer_data, spend_data) DataFrames
    """
    # Customer count data
    sql_customers = """
    SELECT sales_date as ds, customer_count as y
    FROM customers_daily 
    WHERE store_id = ? AND sales_date >= date('now', '-2 years')
    ORDER BY sales_date
    """
    
    # Average spend data
    sql_spend = """
    SELECT sales_date as ds, average_spend as y
    FROM spend_daily 
    WHERE store_id = ? AND sales_date >= date('now', '-2 years')
    ORDER BY sales_date
    """
    
    customer_data = _fetch_df(sql_customers, (store_id,), db_path)
    spend_data = _fetch_df(sql_spend, (store_id,), db_path)
    
    # Convert date columns
    if not customer_data.empty:
        customer_data['ds'] = pd.to_datetime(customer_data['ds'])
    if not spend_data.empty:
        spend_data['ds'] = pd.to_datetime(spend_data['ds'])
    
    return customer_data, spend_data


def _create_prophet_forecast(data: pd.DataFrame, periods: int = 180) -> Tuple[pd.DataFrame, Prophet]:
    """
    Create Prophet forecast for 6 months
    
    Args:
        data: DataFrame with 'ds' and 'y' columns
        periods: Number of days to forecast
        
    Returns:
        Tuple of (forecast_df, fitted_model)
    """
    if data.empty or len(data) < 10:
        return pd.DataFrame(), None
    
    try:
        # Initialize and fit Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(data)
        
        # Create future dataframe for 6 months
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        return forecast, model
    except Exception as e:
        logger.error(f"Error creating Prophet forecast: {e}")
        return pd.DataFrame(), None


def _create_forecast_chart(customer_forecast: pd.DataFrame, spend_forecast: pd.DataFrame, 
                          customer_data: pd.DataFrame, spend_data: pd.DataFrame) -> str:
    """
    Create forecast chart and return as base64 PNG
    
    Args:
        customer_forecast: Customer count forecast
        spend_forecast: Average spend forecast
        customer_data: Historical customer data
        spend_data: Historical spend data
        
    Returns:
        Base64 encoded PNG string
    """
    try:
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('顧客数予測', '客単価予測'),
            vertical_spacing=0.1
        )
        
        # Customer forecast plot
        if not customer_forecast.empty and not customer_data.empty:
            # Historical data
            fig.add_trace(
                go.Scatter(
                    x=customer_data['ds'],
                    y=customer_data['y'],
                    name='実績（顧客数）',
                    line=dict(color='#2E86AB'),
                    mode='lines'
                ),
                row=1, col=1
            )
            
            # Forecast
            future_dates = customer_forecast[customer_forecast['ds'] > customer_data['ds'].max()]
            fig.add_trace(
                go.Scatter(
                    x=future_dates['ds'],
                    y=future_dates['yhat'],
                    name='予測（顧客数）',
                    line=dict(color='#F18F01', dash='dash'),
                    mode='lines'
                ),
                row=1, col=1
            )
            
            # Confidence interval
            fig.add_trace(
                go.Scatter(
                    x=future_dates['ds'].tolist() + future_dates['ds'].tolist()[::-1],
                    y=future_dates['yhat_upper'].tolist() + future_dates['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(241, 143, 1, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='信頼区間（顧客数）',
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Spend forecast plot
        if not spend_forecast.empty and not spend_data.empty:
            # Historical data
            fig.add_trace(
                go.Scatter(
                    x=spend_data['ds'],
                    y=spend_data['y'],
                    name='実績（客単価）',
                    line=dict(color='#A23B72'),
                    mode='lines'
                ),
                row=2, col=1
            )
            
            # Forecast
            future_dates = spend_forecast[spend_forecast['ds'] > spend_data['ds'].max()]
            fig.add_trace(
                go.Scatter(
                    x=future_dates['ds'],
                    y=future_dates['yhat'],
                    name='予測（客単価）',
                    line=dict(color='#C73E1D', dash='dash'),
                    mode='lines'
                ),
                row=2, col=1
            )
            
            # Confidence interval
            fig.add_trace(
                go.Scatter(
                    x=future_dates['ds'].tolist() + future_dates['ds'].tolist()[::-1],
                    y=future_dates['yhat_upper'].tolist() + future_dates['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(199, 62, 29, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='信頼区間（客単価）',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            height=600,
            title_text="6か月予測",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        # Convert to PNG and encode as base64
        img_bytes = fig.to_image(format="png", width=800, height=600)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64
    
    except Exception as e:
        logger.error(f"Error creating forecast chart: {e}")
        return ""


def _get_ai_recommendations(store_id: str, kpi_data: Dict[str, Any]) -> str:
    """
    Get AI-generated recommendations from OpenAI
    
    Args:
        store_id: Store identifier
        kpi_data: KPI metrics dictionary
        
    Returns:
        AI-generated recommendations string
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.warning("OpenAI API key not found")
        return _get_mock_recommendations()
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        あなたはフォトスタジオ経営コンサルタントです。以下の店舗データを分析して、マネージャーが今日実行すべき具体的なアクションプランを5つ提案してください。

        店舗ID: {store_id}
        
        現在の指標:
        - 顧客数: {kpi_data['current']['customers']:,.0f}人
        - 客単価: {kpi_data['current']['avg_spend']:,.0f}円
        - 生産性: {kpi_data['current']['productivity']:,.0f}円/時
        
        前月比:
        - 顧客数変化: {((kpi_data['current']['customers'] - kpi_data['prev_month']['customers']) / max(kpi_data['prev_month']['customers'], 1) * 100):+.1f}%
        - 客単価変化: {((kpi_data['current']['avg_spend'] - kpi_data['prev_month']['avg_spend']) / max(kpi_data['prev_month']['avg_spend'], 1) * 100):+.1f}%
        - 生産性変化: {((kpi_data['current']['productivity'] - kpi_data['prev_month']['productivity']) / max(kpi_data['prev_month']['productivity'], 1) * 100):+.1f}%
        
        フォトスタジオ業界の知見を活かして、実行可能で具体的な改善案を箇条書きで5つ提案してください。
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたはフォトスタジオ経営コンサルタントです。実践的で具体的なアドバイスを提供してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error getting AI recommendations: {e}")
        return _get_mock_recommendations()


def _get_mock_recommendations() -> str:
    """Fallback mock recommendations"""
    return """
- スタジオの予約空き状況を確認し、ピークタイムの効率的な運用を検討する
- 顧客満足度調査を実施し、サービス品質の向上点を特定する
- 新規顧客獲得のためのSNSキャンペーンを企画・実行する
- スタッフのスキルアップ研修を計画し、撮影技術の向上を図る
- 季節性商品の提案や限定プランの導入を検討する
"""


def _calculate_change_percentage(current: float, previous: float) -> str:
    """Calculate percentage change with formatting"""
    if previous == 0 or previous is None or current is None:
        return "N/A"
    try:
        change = (current - previous) / previous * 100
        return f"{change:+.1f}%"
    except (TypeError, ZeroDivisionError):
        return "N/A"


def generate(store_id: str, months: int = 3, db_path: str = "codot.db") -> str:
    """
    Generate comprehensive AI-powered store analytics report
    
    Args:
        store_id: Store identifier
        months: Number of months to analyze
        db_path: Path to SQLite database
        
    Returns:
        Markdown formatted report string
    """
    try:
        # Step 1: Query KPI aggregates
        kpi_data = _get_kpi_aggregates(store_id, months, db_path)
        
        # Step 2: Get daily data and create Prophet forecasts
        customer_data, spend_data = _get_daily_data_for_forecast(store_id, db_path)
        customer_forecast, _ = _create_prophet_forecast(customer_data)
        spend_forecast, _ = _create_prophet_forecast(spend_data)
        
        # Step 3: Create forecast chart
        chart_base64 = _create_forecast_chart(customer_forecast, spend_forecast, customer_data, spend_data)
        
        # Step 4: Get AI recommendations
        ai_comments = _get_ai_recommendations(store_id, kpi_data)
        
        # Build Markdown report
        report = f"""# 店舗分析レポート - {store_id}

## 今月の概要

| 指標 | 値 | 前月比 | 前年同月比 |
|------|----|---------|---------| 
| 顧客数 | {kpi_data['current']['customers']:,.0f}人 | {_calculate_change_percentage(kpi_data['current']['customers'], kpi_data['prev_month']['customers'])} | {_calculate_change_percentage(kpi_data['current']['customers'], kpi_data['prev_year']['customers'])} |
| 客単価 | {kpi_data['current']['avg_spend']:,.0f}円 | {_calculate_change_percentage(kpi_data['current']['avg_spend'], kpi_data['prev_month']['avg_spend'])} | {_calculate_change_percentage(kpi_data['current']['avg_spend'], kpi_data['prev_year']['avg_spend'])} |
| 生産性 | {kpi_data['current']['productivity']:,.0f}円/時 | {_calculate_change_percentage(kpi_data['current']['productivity'], kpi_data['prev_month']['productivity'])} | {_calculate_change_percentage(kpi_data['current']['productivity'], kpi_data['prev_year']['productivity'])} |

## 6か月予測グラフ

"""
        
        if chart_base64:
            report += f'<img src="data:image/png;base64,{chart_base64}" alt="6か月予測グラフ" style="max-width: 100%; height: auto;">\n\n'
        else:
            report += "予測グラフの生成に失敗しました。\n\n"
        
        report += f"""## AIコメント

{ai_comments}

---
*レポート生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return f"# エラー\n\nレポート生成中にエラーが発生しました: {str(e)}"


if __name__ == "__main__":
    # Test the report generation
    from lib.kpi import get_store_list
    
    stores = get_store_list()
    if stores:
        test_store = stores[0]
        print(f"Generating report for store: {test_store}")
        report = generate(test_store)
        print(report)
    else:
        print("No stores found for testing") 