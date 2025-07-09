"""
ETL Module
Data loading and transformation for Codot analytics
"""

import os
import pandas as pd
import sqlite_utils
from sqlite_utils import Database
import logging
from typing import List, Dict, Any
import streamlit as st
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


def setup_sample_database():
    """Set up a sample database with Codot store data"""
    db = Database("codot.db")
    
    # Generate sample data for 5 stores
    import random
    from datetime import datetime, timedelta
    
    stores = ['ST001', 'ST002', 'ST003', 'ST004', 'ST005']
    
    # Sample data generation
    sample_data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(365):  # 1年分のデータ
        current_date = base_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        for store in stores:
            # 顧客数データ
            customer_count = random.randint(50, 200) + random.randint(-20, 20)
            
            # 客単価データ  
            avg_spend = random.randint(3000, 8000) + random.randint(-500, 500)
            
            # 売上データ
            sales_amount = customer_count * avg_spend
            
            # 労働時間データ
            work_hours = random.randint(40, 80)
            
            sample_data.append({
                'sales_date': date_str,
                'store_id': store,
                'customer_count': customer_count,
                'average_spend': avg_spend,
                'sales_amount': sales_amount,
                'work_hours': work_hours
            })
    
    # Create tables
    try:
        # 顧客数テーブル
        customers_data = [
            {
                'sales_date': row['sales_date'],
                'store_id': row['store_id'],
                'customer_count': row['customer_count']
            }
            for row in sample_data
        ]
        db["customers_daily"].insert_all(customers_data, replace=True)
        
        # 客単価テーブル
        spend_data = [
            {
                'sales_date': row['sales_date'],
                'store_id': row['store_id'],
                'average_spend': row['average_spend']
            }
            for row in sample_data
        ]
        db["spend_daily"].insert_all(spend_data, replace=True)
        
        # 売上テーブル
        sales_data = [
            {
                'sales_date': row['sales_date'],
                'store_id': row['store_id'],
                'sales_amount': row['sales_amount']
            }
            for row in sample_data
        ]
        db["sales_daily"].insert_all(sales_data, replace=True)
        
        # 労働時間テーブル
        labor_data = [
            {
                'sales_date': row['sales_date'],
                'store_id': row['store_id'],
                'work_hours': row['work_hours']
            }
            for row in sample_data
        ]
        db["labor_daily"].insert_all(labor_data, replace=True)
        
        logger.info(f"Sample database created successfully with {len(stores)} stores")
        return f"サンプルデータベースを作成しました（{len(stores)}店舗、{len(sample_data)}レコード）"
        
    except Exception as e:
        logger.error(f"Error creating sample database: {e}")
        return f"サンプルデータベース作成エラー: {str(e)}"


def load_excels(uploaded_files) -> str:
    """
    Load multiple Excel files and process them into the database
    
    Args:
        uploaded_files: List of uploaded Excel files from Streamlit
        
    Returns:
        Summary string of the loading process
    """
    if not uploaded_files:
        return "ファイルが選択されていません"
    
    try:
        st.write("🔍 デバッグ情報:")
        st.write(f"アップロードファイル数: {len(uploaded_files)}")
        
        db = Database("codot.db")
        total_records = 0
        processed_files = []
        errors = []
        
        for uploaded_file in uploaded_files:
            try:
                st.write(f"📁 処理中: {uploaded_file.name}")
                
                # Read Excel file
                df = pd.read_excel(uploaded_file)
                st.write(f"  - 行数: {len(df)}")
                st.write(f"  - 列: {list(df.columns)}")
                
                # Display first few rows for debugging
                st.write("  - データサンプル:")
                st.dataframe(df.head(3))
                
                # Data validation and processing
                processed_data = process_excel_data(df, uploaded_file.name)
                
                if processed_data:
                    # Insert into database
                    insert_result = insert_to_database(db, processed_data)
                    total_records += len(processed_data)
                    processed_files.append(uploaded_file.name)
                    st.write(f"  ✅ 正常処理: {len(processed_data)}レコード")
                else:
                    errors.append(f"{uploaded_file.name}: データ処理に失敗")
                    st.write(f"  ❌ エラー: データ処理失敗")
                    
            except Exception as e:
                error_msg = f"{uploaded_file.name}: {str(e)}"
                errors.append(error_msg)
                st.write(f"  ❌ エラー: {str(e)}")
                st.write(f"  詳細: {traceback.format_exc()}")
        
        # Check database content
        try:
            tables = list(db.table_names())
            st.write(f"📊 データベーステーブル: {tables}")
            
            for table in ['customers_daily', 'spend_daily', 'sales_daily', 'labor_daily']:
                if table in tables:
                    count = db[table].count
                    st.write(f"  - {table}: {count}レコード")
                else:
                    st.write(f"  - {table}: テーブル未作成")
        except Exception as e:
            st.write(f"❌ データベース確認エラー: {str(e)}")
        
        # Summary
        summary_parts = []
        if processed_files:
            summary_parts.append(f"成功: {len(processed_files)}ファイル")
        if errors:
            summary_parts.append(f"エラー: {len(errors)}ファイル")
        if total_records > 0:
            summary_parts.append(f"総レコード数: {total_records}")
            
        if errors:
            st.error("エラー詳細:")
            for error in errors:
                st.error(f"  - {error}")
        
        return " | ".join(summary_parts) if summary_parts else "処理結果なし"
        
    except Exception as e:
        error_msg = f"ファイル処理エラー: {str(e)}"
        st.error(error_msg)
        st.error(f"詳細: {traceback.format_exc()}")
        return error_msg


def process_excel_data(df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
    """
    Process Excel data and extract relevant information
    
    Args:
        df: DataFrame from Excel file
        filename: Name of the source file
        
    Returns:
        List of processed records
    """
    try:
        processed_data = []
        
        # Try to detect data format
        st.write(f"🔍 データ形式分析中...")
        
        # Check for required columns (flexible matching)
        date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['date', '日付', '年月日', 'sales_date'])]
        store_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['store', '店舗', 'shop', 'store_id'])]
        customer_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['customer', '顧客', '客数', 'customer_count'])]
        spend_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['spend', '単価', '客単価', 'average_spend'])]
        sales_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['sales', '売上', '売上金額', 'sales_amount'])]
        hours_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['hour', '時間', '労働', 'work_hours'])]
        
        st.write(f"  - 日付列候補: {date_cols}")
        st.write(f"  - 店舗列候補: {store_cols}")
        st.write(f"  - 顧客数列候補: {customer_cols}")
        st.write(f"  - 客単価列候補: {spend_cols}")
        st.write(f"  - 売上列候補: {sales_cols}")
        st.write(f"  - 労働時間列候補: {hours_cols}")
        
        if not date_cols or not store_cols:
            st.warning("必要な列（日付・店舗）が見つかりません")
            return []
        
        # Extract data
        for _, row in df.iterrows():
            try:
                # Extract date
                date_val = row[date_cols[0]]
                if pd.isna(date_val):
                    continue
                    
                # Convert date to string format
                if isinstance(date_val, str):
                    sales_date = date_val
                else:
                    sales_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                
                # Extract store ID
                store_id = str(row[store_cols[0]]) if not pd.isna(row[store_cols[0]]) else 'UNKNOWN'
                
                # Extract metrics (with defaults)
                customer_count = int(row[customer_cols[0]]) if customer_cols and not pd.isna(row[customer_cols[0]]) else 0
                average_spend = float(row[spend_cols[0]]) if spend_cols and not pd.isna(row[spend_cols[0]]) else 0.0
                sales_amount = float(row[sales_cols[0]]) if sales_cols and not pd.isna(row[sales_cols[0]]) else customer_count * average_spend
                work_hours = float(row[hours_cols[0]]) if hours_cols and not pd.isna(row[hours_cols[0]]) else 8.0
                
                processed_data.append({
                    'sales_date': sales_date,
                    'store_id': store_id,
                    'customer_count': customer_count,
                    'average_spend': average_spend,
                    'sales_amount': sales_amount,
                    'work_hours': work_hours
                })
                
            except Exception as e:
                st.warning(f"行データ処理エラー: {str(e)}")
                continue
        
        st.write(f"✅ 処理完了: {len(processed_data)}レコード")
        return processed_data
        
    except Exception as e:
        st.error(f"データ処理エラー: {str(e)}")
        return []


def insert_to_database(db: Database, data: List[Dict[str, Any]]) -> bool:
    """
    Insert processed data into database tables
    
    Args:
        db: Database instance
        data: Processed data records
        
    Returns:
        Success status
    """
    try:
        # Separate data by table
        customers_data = []
        spend_data = []
        sales_data = []
        labor_data = []
        
        for record in data:
            customers_data.append({
                'sales_date': record['sales_date'],
                'store_id': record['store_id'],
                'customer_count': record['customer_count']
            })
            
            spend_data.append({
                'sales_date': record['sales_date'],
                'store_id': record['store_id'],
                'average_spend': record['average_spend']
            })
            
            sales_data.append({
                'sales_date': record['sales_date'],
                'store_id': record['store_id'],
                'sales_amount': record['sales_amount']
            })
            
            labor_data.append({
                'sales_date': record['sales_date'],
                'store_id': record['store_id'],
                'work_hours': record['work_hours']
            })
        
        # Insert into tables
        if customers_data:
            db["customers_daily"].insert_all(customers_data, replace=True)
        if spend_data:
            db["spend_daily"].insert_all(spend_data, replace=True)
        if sales_data:
            db["sales_daily"].insert_all(sales_data, replace=True)
        if labor_data:
            db["labor_daily"].insert_all(labor_data, replace=True)
        
        return True
        
    except Exception as e:
        st.error(f"データベース挿入エラー: {str(e)}")
        return False 