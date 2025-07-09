"""
ETL (Extract, Transform, Load) Module
Handles data extraction, transformation, and loading operations
"""

import pandas as pd
import sqlite3
from sqlite_utils import Database
from typing import Dict, List, Any, Optional, Union
import logging
import os
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class DataExtractor:
    """Handles data extraction from various sources"""
    
    def __init__(self, db_path: str = "codot_data.db"):
        self.db_path = db_path
        self.db = Database(db_path)
    
    def extract_from_sqlite(self, query: str) -> pd.DataFrame:
        """Extract data from SQLite database"""
        try:
            return pd.read_sql_query(query, sqlite3.connect(self.db_path))
        except Exception as e:
            logger.error(f"Error extracting data from SQLite: {e}")
            return pd.DataFrame()
    
    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """Extract data from CSV file"""
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return pd.DataFrame()

class DataTransformer:
    """Handles data transformation operations"""
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize data"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = df.fillna(method='ffill')
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        return df
    
    @staticmethod
    def aggregate_data(df: pd.DataFrame, group_by: List[str], 
                      agg_dict: Dict[str, Any]) -> pd.DataFrame:
        """Aggregate data based on specified columns"""
        try:
            return df.groupby(group_by).agg(agg_dict).reset_index()
        except Exception as e:
            logger.error(f"Error aggregating data: {e}")
            return df

class DataLoader:
    """Handles data loading operations"""
    
    def __init__(self, db_path: str = "codot_data.db"):
        self.db = Database(db_path)
    
    def load_to_sqlite(self, df: pd.DataFrame, table_name: str, 
                      if_exists: str = "replace") -> bool:
        """Load data to SQLite database"""
        try:
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Insert data using sqlite-utils
            self.db[table_name].insert_all(records, replace=True if if_exists=="replace" else False)
            
            logger.info(f"Successfully loaded {len(records)} records to {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading data to SQLite: {e}")
            return False

def load_data(source: str = "database") -> pd.DataFrame:
    """Main function to load data from specified source"""
    extractor = DataExtractor()
    transformer = DataTransformer()
    
    if source == "database":
        # Sample query - adjust based on your actual database schema
        query = """
        SELECT 
            date,
            user_id,
            project_id,
            commits,
            lines_added,
            lines_deleted
        FROM activity_log 
        WHERE date >= date('now', '-30 days')
        """
        df = extractor.extract_from_sqlite(query)
    elif source == "csv":
        # Load from CSV file
        df = extractor.extract_from_csv("data/sample_data.csv")
    else:
        # Return sample data if no source specified
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'user_id': range(1, 31),
            'project_id': [1, 2, 3] * 10,
            'commits': pd.np.random.randint(1, 10, 30),
            'lines_added': pd.np.random.randint(10, 500, 30),
            'lines_deleted': pd.np.random.randint(5, 200, 30)
        })
    
    # Transform the data
    df = transformer.clean_data(df)
    
    return df

def setup_sample_database():
    """Set up a sample database with Codot store data"""
    db = Database("codot.db")
    
    # Generate sample dates (last 90 days)
    from datetime import datetime, timedelta
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(90, 0, -1)]
    stores = ['ST001', 'ST002', 'ST003']
    
    # Sales data
    sales_data = []
    for store in stores:
        for i, date in enumerate(dates):
            sales_data.append({
                'sales_date': date,
                'store_id': store, 
                'sales_amount': 45000 + (i % 10) * 5000 + (hash(store) % 20000)
            })
    
    # Customer data
    customer_data = []
    for store in stores:
        for i, date in enumerate(dates):
            customer_data.append({
                'sales_date': date,
                'store_id': store,
                'customer_count': 18 + (i % 8) * 2 + (hash(store) % 10)
            })
    
    # Spend data  
    spend_data = []
    for store in stores:
        for i, date in enumerate(dates):
            spend_data.append({
                'sales_date': date,
                'store_id': store,
                'average_spend': 2200 + (i % 12) * 150 + (hash(store) % 800)
            })
    
    # Labor data
    labor_data = []
    for store in stores:
        for i, date in enumerate(dates):
            labor_data.append({
                'sales_date': date,
                'store_id': store,
                'work_hours': 7.5 + (i % 5) * 0.5 + (hash(store) % 3)
            })
    
    # Insert sample data into respective tables
    db["sales_daily"].insert_all(sales_data, replace=True)
    db["customers_daily"].insert_all(customer_data, replace=True) 
    db["spend_daily"].insert_all(spend_data, replace=True)
    db["labor_daily"].insert_all(labor_data, replace=True)
    
    logger.info(f"Sample database created with {len(stores)} stores and {len(dates)} days of data")

# Codot Excel Processing Functions

def normalise_municipality(municipality_name: str, master_csv_path: str = "data/municipality_master.csv") -> str:
    """
    Normalize municipality name using master CSV file
    
    Args:
        municipality_name: Input municipality name (possibly with variations)
        master_csv_path: Path to municipality master CSV file
        
    Returns:
        Standardized municipality name
    """
    try:
        if municipality_name is None or municipality_name == '' or pd.isna(municipality_name):
            return municipality_name
    except (TypeError, ValueError):
        if municipality_name is None or municipality_name == '':
            return municipality_name
    
    # Clean input
    clean_name = str(municipality_name).strip()
    
    try:
        # Load municipality master if exists
        if os.path.exists(master_csv_path):
            master_df = pd.read_csv(master_csv_path)
        else:
            logger.warning(f"Municipality master file not found: {master_csv_path}")
            return clean_name
        
        # Search through all variant columns
        for _, row in master_df.iterrows():
            # Check standard name first
            if clean_name == row['standard_name']:
                return row['standard_name']
            
            # Check all variant columns
            for col in ['variant_1', 'variant_2', 'variant_3', 'variant_4']:
                if pd.notna(row[col]) and clean_name == row[col]:
                    return row['standard_name']
        
        # If no exact match, try partial matching (case insensitive)
        clean_lower = clean_name.lower()
        for _, row in master_df.iterrows():
            variants = [row['standard_name']] + [row[col] for col in ['variant_1', 'variant_2', 'variant_3', 'variant_4'] if pd.notna(row[col])]
            for variant in variants:
                if clean_lower in variant.lower() or variant.lower() in clean_lower:
                    return row['standard_name']
        
    except Exception as e:
        logger.error(f"Error normalizing municipality '{municipality_name}': {e}")
    
    return clean_name


def standardize_column_names(df: pd.DataFrame, sheet_type: str) -> pd.DataFrame:
    """
    Standardize column names based on sheet type
    
    Args:
        df: Input DataFrame
        sheet_type: Type of sheet ('sales', 'customers', 'spend', 'labor')
        
    Returns:
        DataFrame with standardized column names
    """
    # Common column mappings
    common_mappings = {
        '売上日': 'sales_date',
        '日付': 'sales_date', 
        '店舗名': 'store_id',
        '店舗': 'store_id',
        '市区町村': 'municipality',
        '自治体': 'municipality',
        '地域': 'region'
    }
    
    # Sheet-specific mappings
    sheet_mappings = {
        'sales': {
            '売上合計': 'sales_amount',
            '売上': 'sales_amount',
            '売上高': 'sales_amount',
            '合計売上': 'sales_amount',
            '税込売上': 'sales_amount_tax_included',
            '税抜売上': 'sales_amount_tax_excluded'
        },
        'customers': {
            '顧客数': 'customer_count',
            '来客数': 'customer_count',
            '客数': 'customer_count',
            '新規顧客': 'new_customers',
            'リピート顧客': 'repeat_customers'
        },
        'spend': {
            '客単価': 'average_spend',
            '平均客単価': 'average_spend',
            '単価': 'average_spend',
            '客単': 'average_spend'
        },
        'labor': {
            '勤怠': 'attendance',
            '出勤': 'attendance',
            '労働時間': 'work_hours',
            '時間': 'work_hours',
            '人件費': 'labor_cost',
            '給与': 'salary'
        }
    }
    
    # Combine mappings
    all_mappings = {**common_mappings}
    if sheet_type in sheet_mappings:
        all_mappings.update(sheet_mappings[sheet_type])
    
    # Apply mappings
    df_copy = df.copy()
    df_copy.columns = [all_mappings.get(col, col.lower().replace(' ', '_').replace('　', '_')) 
                       for col in df_copy.columns]
    
    return df_copy


def detect_sheet_type(sheet_name: str) -> Optional[str]:
    """
    Detect sheet type based on sheet name
    
    Args:
        sheet_name: Name of the Excel sheet
        
    Returns:
        Sheet type ('sales', 'customers', 'spend', 'labor') or None
    """
    sheet_name_lower = sheet_name.lower()
    
    if '売上' in sheet_name:
        return 'sales'
    elif '顧客' in sheet_name:
        return 'customers'
    elif '客単価' in sheet_name or '単価' in sheet_name:
        return 'spend'
    elif '勤怠' in sheet_name:
        return 'labor'
    
    return None


def get_table_name(sheet_type: str) -> str:
    """Get SQLite table name for sheet type"""
    table_mapping = {
        'sales': 'sales_daily',
        'customers': 'customers_daily', 
        'spend': 'spend_daily',
        'labor': 'labor_daily'
    }
    return table_mapping.get(sheet_type, f"{sheet_type}_daily")


def upsert_dataframe(df: pd.DataFrame, table_name: str, db_path: str = "codot.db") -> Dict[str, int]:
    """
    Upsert DataFrame to SQLite table based on (sales_date, store_id) primary key
    
    Args:
        df: DataFrame to upsert
        table_name: Target table name
        db_path: SQLite database path
        
    Returns:
        Dictionary with inserted and updated row counts
    """
    if df.empty:
        return {'inserted_rows': 0, 'updated_rows': 0}
    
    # Ensure required columns exist
    required_cols = ['sales_date', 'store_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        return {'inserted_rows': 0, 'updated_rows': 0}
    
    try:
        db = Database(db_path)
        
        # Convert DataFrame to records
        records = df.to_dict('records')
        
        # Check if table exists and get existing records
        if table_name in db.table_names():
            existing_query = f"SELECT sales_date, store_id FROM {table_name}"
            existing_df = pd.read_sql_query(existing_query, sqlite3.connect(db_path))
            existing_keys = set(zip(existing_df['sales_date'], existing_df['store_id']))
        else:
            existing_keys = set()
        
        # Separate new and existing records
        new_records = []
        update_records = []
        
        for record in records:
            key = (record['sales_date'], record['store_id'])
            if key in existing_keys:
                update_records.append(record)
            else:
                new_records.append(record)
        
        # Insert new records
        inserted_count = 0
        if new_records:
            db[table_name].insert_all(new_records)
            inserted_count = len(new_records)
        
        # Update existing records
        updated_count = 0
        if update_records:
            # Use upsert instead of update for better reliability
            db[table_name].upsert_all(
                update_records, 
                pk=['sales_date', 'store_id']
            )
            updated_count = len(update_records)
        
        logger.info(f"Table {table_name}: {inserted_count} inserted, {updated_count} updated")
        return {'inserted_rows': inserted_count, 'updated_rows': updated_count}
        
    except Exception as e:
        logger.error(f"Error upserting to {table_name}: {e}")
        return {'inserted_rows': 0, 'updated_rows': 0}


def load_excels(files: List[Union[str, Any]], db_path: str = "codot.db") -> Dict[str, Dict[str, int]]:
    """
    Accepts a list of uploaded xlsx files from Codot system and upserts into SQLite database.
    
    Sheet rules:
    - シート名に "売上" → sales_daily table
    - "顧客数" → customers_daily table
    - "客単価" → spend_daily table
    - "勤怠" → labor_daily table
    
    Args:
        files: List of Excel file paths or file-like objects
        db_path: SQLite database path (default: "codot.db")
        
    Returns:
        Summary dictionary: {table_name: {'inserted_rows': int, 'updated_rows': int}}
    """
    summary = {}
    
    for file in files:
        try:
            # Read Excel file
            if isinstance(file, str):
                excel_file = pd.ExcelFile(file)
                file_name = os.path.basename(file)
            else:
                # Handle file-like objects (e.g., from Streamlit file uploader)
                excel_file = pd.ExcelFile(file)
                file_name = getattr(file, 'name', 'uploaded_file')
            
            logger.info(f"Processing Excel file: {file_name}")
            
            # Process each sheet
            for sheet_name in excel_file.sheet_names:
                logger.info(f"Processing sheet: {sheet_name}")
                
                # Detect sheet type
                sheet_type = detect_sheet_type(sheet_name)
                if not sheet_type:
                    logger.warning(f"Unknown sheet type for '{sheet_name}', skipping")
                    continue
                
                # Read sheet data
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Drop completely empty rows
                df = df.dropna(how='all')
                
                if df.empty:
                    logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                # Standardize column names
                df = standardize_column_names(df, sheet_type)
                
                # Normalize municipality names if column exists
                if 'municipality' in df.columns:
                    df['municipality'] = df['municipality'].apply(normalise_municipality)
                
                # Convert sales_date to proper date format
                if 'sales_date' in df.columns:
                    try:
                        df['sales_date'] = pd.to_datetime(df['sales_date']).dt.strftime('%Y-%m-%d')
                    except Exception as e:
                        logger.warning(f"Error converting sales_date: {e}")
                        df['sales_date'] = df['sales_date'].astype(str)
                
                # Get table name
                table_name = get_table_name(sheet_type)
                
                # Upsert data
                result = upsert_dataframe(df, table_name, db_path)
                
                # Update summary
                if table_name not in summary:
                    summary[table_name] = {'inserted_rows': 0, 'updated_rows': 0}
                
                summary[table_name]['inserted_rows'] += result['inserted_rows']
                summary[table_name]['updated_rows'] += result['updated_rows']
                
        except Exception as e:
            logger.error(f"Error processing Excel file {getattr(file, 'name', str(file))}: {e}")
            continue
    
    return summary


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Auto mode: process files from command line arguments
        if len(sys.argv) < 3:
            print("Usage: python -m lib.etl --auto <file1.xlsx> [file2.xlsx] ...")
            sys.exit(1)
        
        files = sys.argv[2:]
        print(f"Processing {len(files)} files in auto mode...")
        summary = load_excels(files)
        
        total_inserted = sum(table['inserted_rows'] for table in summary.values())
        total_updated = sum(table['updated_rows'] for table in summary.values())
        
        print(f"ETL completed: {total_inserted} rows inserted, {total_updated} rows updated")
        for table_name, stats in summary.items():
            print(f"  {table_name}: {stats['inserted_rows']} inserted, {stats['updated_rows']} updated")
    else:
        # Interactive mode
        setup_sample_database()
        data = load_data()
        print(data.head()) 