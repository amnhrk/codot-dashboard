#!/bin/bash

# Codot Excel Files Download Script
# Downloads the latest Codot Excel files for ETL processing

set -e  # Exit on any error

# Configuration
DOWNLOAD_DIR="./temp_downloads"
LOG_FILE="download.log"

# Create download directory
mkdir -p "$DOWNLOAD_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Codot file download..."

# Simulate download process (replace with actual download logic)
# In production, this would connect to Codot API or file server

# Mock download - create sample files for demonstration
log "Downloading latest Codot files..."

# Example: Download from API or file server
# curl -H "Authorization: Bearer $CODOT_API_KEY" \
#      -o "$DOWNLOAD_DIR/sales_$(date +%Y%m%d).xlsx" \
#      "https://api.codot.com/reports/sales/latest"

# For now, create mock files if they don't exist
SAMPLE_FILES=(
    "$DOWNLOAD_DIR/codot_sales_$(date +%Y%m%d).xlsx"
    "$DOWNLOAD_DIR/codot_customers_$(date +%Y%m%d).xlsx"
    "$DOWNLOAD_DIR/codot_spend_$(date +%Y%m%d).xlsx"
    "$DOWNLOAD_DIR/codot_labor_$(date +%Y%m%d).xlsx"
)

# Create sample Excel files (in production, replace with actual download)
if [ ! -f "${SAMPLE_FILES[0]}" ]; then
    log "Creating sample files for demonstration..."
    python3 -c "
import pandas as pd
import os
from datetime import datetime, timedelta

download_dir = '$DOWNLOAD_DIR'
today = datetime.now()

# Sample data generation
dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
stores = ['ST001', 'ST002', 'ST003']

for store in stores:
    # Sales data
    sales_data = pd.DataFrame({
        '売上日': dates,
        '店舗ID': [store] * len(dates),
        '売上金額': [50000 + (i % 10) * 5000 for i in range(len(dates))]
    })
    
    # Customer data  
    customer_data = pd.DataFrame({
        '売上日': dates,
        '店舗ID': [store] * len(dates),
        '顧客数': [20 + (i % 5) * 3 for i in range(len(dates))]
    })
    
    # Spend data
    spend_data = pd.DataFrame({
        '売上日': dates,
        '店舗ID': [store] * len(dates),
        '客単価': [2500 + (i % 8) * 200 for i in range(len(dates))]
    })
    
    # Labor data
    labor_data = pd.DataFrame({
        '売上日': dates,
        '店舗ID': [store] * len(dates),
        '労働時間': [8.0 + (i % 3) * 0.5 for i in range(len(dates))]
    })
    
    # Write to Excel files
    with pd.ExcelWriter(f'{download_dir}/codot_{store}_$(date +%Y%m%d).xlsx') as writer:
        sales_data.to_excel(writer, sheet_name='売上データ', index=False)
        customer_data.to_excel(writer, sheet_name='顧客数データ', index=False)
        spend_data.to_excel(writer, sheet_name='客単価データ', index=False)
        labor_data.to_excel(writer, sheet_name='勤怠データ', index=False)

print('Sample files created successfully')
"
fi

# List downloaded files
DOWNLOADED_FILES=$(find "$DOWNLOAD_DIR" -name "*.xlsx" -mtime -1 2>/dev/null || echo "")

if [ -z "$DOWNLOADED_FILES" ]; then
    log "No new files downloaded"
    echo ""  # Return empty string if no files
else
    log "Downloaded files:"
    echo "$DOWNLOADED_FILES" | while read -r file; do
        log "  - $(basename "$file")"
    done
    
    # Return space-separated list of files for ETL processing
    echo "$DOWNLOADED_FILES" | tr '\n' ' '
fi

log "Download process completed" 