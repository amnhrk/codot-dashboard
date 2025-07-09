"""
ETL Module
Data loading and transformation for Codot analytics
Enhanced to handle multiple Excel formats
"""

import os
import pandas as pd
import sqlite_utils
from sqlite_utils import Database
import logging
from typing import List, Dict, Any, Optional
import streamlit as st
from datetime import datetime
import traceback
import re

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


def smart_read_excel(uploaded_file) -> pd.DataFrame:
    """
    Smart Excel reader that handles various file formats
    """
    st.write("🚀 **DEBUG: smart_read_excel関数が呼び出されました**")
    try:
        # Try reading with different header positions
        possible_dfs = []
        
        # Try header at row 0 through 15 to handle complex Excel layouts
        for header_row in range(16):
            try:
                df = pd.read_excel(uploaded_file, header=header_row, skiprows=0)
                
                # Check if this looks like a valid data frame
                if len(df.columns) > 0 and len(df) > 0:
                    # Count how many columns have meaningful names (not Unnamed)
                    meaningful_cols = sum(1 for col in df.columns if not str(col).startswith('Unnamed') and not pd.isna(col) and str(col).strip())
                    unnamed_cols = sum(1 for col in df.columns if str(col).startswith('Unnamed'))
                    
                    # Count non-null data
                    non_null_data = df.count().sum()
                    total_cells = len(df) * len(df.columns)
                    data_ratio = non_null_data / max(total_cells, 1)
                    
                    # Enhanced scoring
                    score = meaningful_cols * 20 + non_null_data + data_ratio * 100 - unnamed_cols * 10
                    possible_dfs.append((score, header_row, df, meaningful_cols, unnamed_cols, non_null_data))
                    
            except Exception as e:
                continue
        
        if possible_dfs:
            # Sort by score and pick the best one
            possible_dfs.sort(key=lambda x: x[0], reverse=True)
            
            # Show all attempts for debugging
            st.write("🔍 **ヘッダー検索結果**:")
            for i, (score, header_row, df, meaningful, unnamed, non_null) in enumerate(possible_dfs[:5]):
                st.write(f"  {i+1}. 行{header_row}: スコア{score:.1f} (有効:{meaningful}, 不明:{unnamed}, データ:{non_null})")
                if i < 3:  # Show columns for top 3 candidates
                    cols_preview = list(df.columns)[:5]
                    st.write(f"     列名例: {cols_preview}")
            
            best_score, best_header, best_df, meaningful, unnamed, non_null = possible_dfs[0]
            
            st.write(f"📊 **選択されたヘッダー行**: {best_header}行目")
            st.write(f"   - 有効列名: {meaningful}個")
            st.write(f"   - 不明列名: {unnamed}個") 
            st.write(f"   - 非空データ: {non_null}個")
            st.write(f"   - 実際の列名: {list(best_df.columns)}")
            
            return best_df
        else:
            # Fallback to standard read
            return pd.read_excel(uploaded_file)
            
    except Exception as e:
        st.error(f"Excelファイル読み込みエラー: {str(e)}")
        return None


def detect_column_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Enhanced column detection with Japanese and English patterns
    """
    columns = df.columns.tolist()
    mapping = {
        'date': None,
        'store': None,
        'customer': None,
        'spend': None,
        'sales': None,
        'hours': None
    }
    
    # Enhanced detection patterns with more Japanese variations
    patterns = {
        'date': [
            r'.*日付.*', r'.*date.*', r'.*年月日.*', r'.*sales_date.*',
            r'.*販売日.*', r'.*売上日.*', r'.*取引日.*', r'.*営業日.*',
            r'.*年月.*', r'.*月日.*', r'.*時期.*'
        ],
        'store': [
            r'.*店舗.*', r'.*store.*', r'.*shop.*', r'.*店.*',
            r'.*支店.*', r'.*branch.*', r'.*店舗id.*', r'.*store_id.*',
            r'.*拠点.*', r'.*営業所.*', r'.*店名.*'
        ],
                 'customer': [
             r'.*顧客.*', r'.*客数.*', r'.*customer.*', r'.*来客.*',
             r'.*customer_count.*', r'.*visitors.*', r'.*来店.*',
             r'.*人数.*', r'.*客.*', r'.*訪問.*', r'^客数$', r'^顧客数$'
         ],
                 'spend': [
             r'.*客単価.*', r'.*単価.*', r'.*spend.*', r'.*average.*',
             r'.*客平均.*', r'.*avg.*', r'.*一人当.*', r'.*平均単価.*',
             r'.*unit_price.*', r'.*per_customer.*', r'.*契約価.*',
             r'.*価格.*', r'.*金額.*', r'.*料金.*'
         ],
        'sales': [
            r'.*売上.*', r'.*sales.*', r'.*revenue.*', r'.*売上金額.*',
            r'.*sales_amount.*', r'.*total.*', r'.*金額.*',
            r'.*収益.*', r'.*売上高.*'
        ],
        'hours': [
            r'.*時間.*', r'.*hour.*', r'.*労働.*', r'.*work.*',
            r'.*勤務.*', r'.*営業時間.*', r'.*稼働.*'
        ]
    }
    
    # Match columns to patterns
    for key, pattern_list in patterns.items():
        best_match = None
        best_score = 0
        
        for col in columns:
            col_str = str(col).lower().replace(' ', '').replace('_', '')
            for pattern in pattern_list:
                if re.search(pattern, col_str, re.IGNORECASE):
                    # Score based on pattern specificity
                    score = len(pattern) - pattern.count('.*')
                    if score > best_score:
                        best_score = score
                        best_match = col
        
        if best_match:
            mapping[key] = best_match
    
    return mapping


def analyze_data_quality(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """
    Analyze data quality and provide insights
    """
    analysis = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'empty_rows': 0,
        'column_issues': [],
        'data_types': {},
        'sample_data': {}
    }
    
    # Count empty rows
    analysis['empty_rows'] = df.isnull().all(axis=1).sum()
    
    # Analyze each mapped column
    for key, col_name in mapping.items():
        if col_name and col_name in df.columns:
            col_data = df[col_name]
            analysis['data_types'][key] = str(col_data.dtype)
            
            # Get sample non-null values
            non_null_values = col_data.dropna().head(3).tolist()
            analysis['sample_data'][key] = non_null_values
            
            # Check for issues
            null_count = col_data.isnull().sum()
            if null_count > len(df) * 0.5:  # More than 50% null
                analysis['column_issues'].append(f"{key}列({col_name}): {null_count}個の空値")
        else:
            analysis['column_issues'].append(f"{key}列: 検出されませんでした")
    
    return analysis


def validate_and_convert_data(df: pd.DataFrame, mapping: Dict[str, Optional[str]], filename: str) -> List[Dict[str, Any]]:
    """
    Validate and convert data with flexible format handling
    """
    processed_data = []
    errors = []
    
    # Check essential columns
    if not mapping['date'] or not mapping['store']:
        errors.append("必須列（日付・店舗）が見つかりません")
        return []
    
    st.write(f"📋 **{filename}** の列マッピング:")
    for key, col in mapping.items():
        if col:
            st.write(f"  - {key}: `{col}`")
        else:
            st.write(f"  - {key}: ❌ 未検出")
    
    # Process each row
    success_count = 0
    for idx, row in df.iterrows():
        try:
            # Extract and validate date
            date_val = row[mapping['date']]
            if pd.isna(date_val):
                continue
                
            # Multiple date format support
            try:
                if isinstance(date_val, str):
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            sales_date = datetime.strptime(date_val, fmt).strftime('%Y-%m-%d')
                            break
                        except:
                            continue
                    else:
                        # If no format matches, try pandas
                        sales_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                else:
                    sales_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
            except:
                errors.append(f"行{idx+1}: 日付形式エラー ({date_val})")
                continue
            
            # Extract store ID with cleaning
            store_val = row[mapping['store']]
            if pd.isna(store_val):
                continue
            store_id = str(store_val).strip()
            
            # Extract metrics with defaults and validation
            customer_count = 0
            if mapping['customer']:
                try:
                    val = row[mapping['customer']]
                    customer_count = int(float(val)) if not pd.isna(val) else 0
                except:
                    pass
            
            average_spend = 0.0
            if mapping['spend']:
                try:
                    val = row[mapping['spend']]
                    average_spend = float(val) if not pd.isna(val) else 0.0
                except:
                    pass
            
            sales_amount = 0.0
            if mapping['sales']:
                try:
                    val = row[mapping['sales']]
                    sales_amount = float(val) if not pd.isna(val) else 0.0
                except:
                    pass
            
            # Calculate missing values
            if sales_amount == 0 and customer_count > 0 and average_spend > 0:
                sales_amount = customer_count * average_spend
            elif average_spend == 0 and customer_count > 0 and sales_amount > 0:
                average_spend = sales_amount / customer_count
            
            work_hours = 8.0  # Default
            if mapping['hours']:
                try:
                    val = row[mapping['hours']]
                    work_hours = float(val) if not pd.isna(val) else 8.0
                except:
                    pass
            
            processed_data.append({
                'sales_date': sales_date,
                'store_id': store_id,
                'customer_count': customer_count,
                'average_spend': average_spend,
                'sales_amount': sales_amount,
                'work_hours': work_hours
            })
            success_count += 1
            
        except Exception as e:
            errors.append(f"行{idx+1}: {str(e)}")
            continue
    
    # Display results
    st.write(f"✅ 正常処理: {success_count}行")
    if errors:
        st.write(f"⚠️ エラー: {len(errors)}行")
        with st.expander("エラー詳細"):
            for error in errors[:10]:  # Show first 10 errors
                st.write(f"  - {error}")
            if len(errors) > 10:
                st.write(f"  - ...他{len(errors)-10}件")
    
    return processed_data


def load_excels(uploaded_files) -> str:
    """
    Enhanced Excel loader with better diagnostics
    """
    if not uploaded_files:
        return "ファイルが選択されていません"
    
    try:
        st.write("📊 **ファイル処理開始**")
        st.write(f"アップロードファイル数: {len(uploaded_files)}")
        
        db = Database("codot.db")
        total_records = 0
        processed_files = []
        file_results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            st.write(f"\n---\n## 📁 {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
            
            try:
                # Smart Excel reading
                df = smart_read_excel(uploaded_file)
                
                if df is None or df.empty:
                    file_results.append(f"❌ {uploaded_file.name}: ファイル読み込み失敗")
                    st.error("❌ ファイルを読み込めませんでした")
                    continue
                
                st.write(f"**基本情報**: {len(df)}行 × {len(df.columns)}列")
                
                # Show column list with types
                st.write("**列一覧**:")
                for col in df.columns:
                    dtype = df[col].dtype
                    non_null = df[col].count()
                    st.write(f"  - `{col}` ({dtype}): {non_null}個の有効データ")
                
                # Show data sample (first few rows with actual data)
                st.write("**データサンプル**:")
                # Find first row with substantial data
                for idx in range(min(5, len(df))):
                    row_data = df.iloc[idx]
                    non_null_count = row_data.count()
                    if non_null_count > len(df.columns) * 0.3:  # At least 30% of columns have data
                        sample_df = df.iloc[idx:idx+3] if idx+3 <= len(df) else df.iloc[idx:]
                        st.dataframe(sample_df)
                        break
                else:
                    st.dataframe(df.head(3))
                
                # Detect column mapping
                mapping = detect_column_mapping(df)
                
                # Data quality analysis
                analysis = analyze_data_quality(df, mapping)
                
                # Display mapping and analysis
                st.write(f"📋 **列マッピング結果**:")
                for key, col in mapping.items():
                    if col:
                        sample_data = analysis['sample_data'].get(key, [])
                        sample_str = ', '.join(str(x) for x in sample_data[:2])
                        st.write(f"  - {key}: `{col}` (例: {sample_str})")
                    else:
                        st.write(f"  - {key}: ❌ 未検出")
                
                # Show data quality issues
                if analysis['column_issues']:
                    st.warning("⚠️ **データ品質の問題**:")
                    for issue in analysis['column_issues']:
                        st.write(f"  - {issue}")
                
                # Validate and process data
                processed_data = validate_and_convert_data(df, mapping, uploaded_file.name)
                
                if processed_data:
                    # Insert into database
                    success = insert_to_database(db, processed_data)
                    if success:
                        total_records += len(processed_data)
                        processed_files.append(uploaded_file.name)
                        file_results.append(f"✅ {uploaded_file.name}: {len(processed_data)}レコード")
                        st.success(f"✅ 処理完了: {len(processed_data)}レコード")
                    else:
                        file_results.append(f"❌ {uploaded_file.name}: DB挿入エラー")
                        st.error("❌ データベース挿入に失敗")
                else:
                    file_results.append(f"⚠️ {uploaded_file.name}: データ処理失敗")
                    st.warning("⚠️ 有効なデータが見つかりませんでした")
                    
            except Exception as e:
                error_msg = f"❌ {uploaded_file.name}: {str(e)}"
                file_results.append(error_msg)
                st.error(f"❌ ファイル処理エラー: {str(e)}")
                st.write("**詳細エラー情報**:")
                st.code(traceback.format_exc())
        
        # Final summary
        st.write("\n---\n## 📋 **処理結果サマリー**")
        for result in file_results:
            st.write(f"- {result}")
        
        if total_records > 0:
            st.write(f"\n**合計**: {total_records}レコード処理完了")
            
            # Check database status
            try:
                stores = list(db.execute("SELECT DISTINCT store_id FROM customers_daily"))
                store_ids = [store['store_id'] for store in stores]
                st.write(f"**登録店舗**: {store_ids}")
            except:
                pass
        
        return f"処理完了: {len(processed_files)}/{len(uploaded_files)}ファイル成功"
        
    except Exception as e:
        error_msg = f"システムエラー: {str(e)}"
        st.error(error_msg)
        return error_msg


def insert_to_database(db: Database, data: List[Dict[str, Any]]) -> bool:
    """
    Insert processed data into database tables
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
        
        # Insert into tables (append mode to handle multiple files)
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