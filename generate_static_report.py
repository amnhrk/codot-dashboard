#!/usr/bin/env python3
"""
Codot Dashboard Static Report Generator
Xサーバー等の静的ホスティング用HTMLレポート生成
"""

import os
import sqlite3
from datetime import datetime
import base64
from io import BytesIO

# 必要に応じて依存関係をインポート
try:
    from lib.etl import setup_sample_database
    from lib.kpi import get_store_list, plot_customer_trend, plot_spend_trend, plot_productivity
    from lib.ai_comment import generate
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please run: poetry install")
    exit(1)

def generate_static_html():
    """静的HTMLレポートを生成"""
    print("📊 Generating static HTML report...")
    
    # データベース準備
    setup_sample_database()
    stores = get_store_list()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📸 Codot店舗ダッシュボード</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1f77b4;
                text-align: center;
                margin-bottom: 40px;
            }}
            .store-section {{
                margin-bottom: 50px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }}
            .store-title {{
                background: #1f77b4;
                color: white;
                padding: 15px;
                margin: -20px -20px 20px -20px;
                border-radius: 8px 8px 0 0;
                font-size: 1.2em;
                font-weight: bold;
            }}
            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .chart-container {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }}
            .ai-report {{
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 20px;
                border-radius: 5px;
            }}
            .timestamp {{
                text-align: center;
                color: #666;
                margin-top: 30px;
                border-top: 1px solid #e0e0e0;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📸 キャラット店舗ダッシュボード</h1>
            <p style="text-align: center; color: #666;">生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>
    """
    
    # 各店舗のレポート生成
    for store in stores:
        print(f"🏪 Generating report for store: {store}")
        
        html_content += f"""
            <div class="store-section">
                <div class="store-title">🏪 店舗: {store}</div>
                
                <div class="charts-grid">
                    <div class="chart-container">
                        <div id="customer-chart-{store}"></div>
                    </div>
                    <div class="chart-container">
                        <div id="spend-chart-{store}"></div>
                    </div>
                    <div class="chart-container">
                        <div id="productivity-chart-{store}"></div>
                    </div>
                </div>
                
                <div class="ai-report">
                    <h3>🤖 AI分析レポート</h3>
                    {generate(store, 3)}
                </div>
            </div>
        """
        
        # Plotlyグラフのスクリプト追加
        html_content += f"""
        <script>
            // 顧客数トレンド
            var customerData = {plot_customer_trend(store, 3).to_json()};
            Plotly.newPlot('customer-chart-{store}', customerData.data, customerData.layout);
            
            // 客単価トレンド  
            var spendData = {plot_spend_trend(store, 3).to_json()};
            Plotly.newPlot('spend-chart-{store}', spendData.data, spendData.layout);
            
            // 生産性トレンド
            var productivityData = {plot_productivity(store, 3).to_json()};
            Plotly.newPlot('productivity-chart-{store}', productivityData.data, productivityData.layout);
        </script>
        """
    
    html_content += f"""
            <div class="timestamp">
                <p>🔄 最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p>📊 データソース: Codot データベース</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # HTMLファイル保存
    output_file = "codot_dashboard_report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Static HTML report generated: {output_file}")
    print(f"📁 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print("🌐 Ready for upload to Xserver!")
    
    return output_file

if __name__ == "__main__":
    os.environ['OPENAI_API_KEY'] = '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'
    generate_static_html() 