import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# Load the dataset
def load_data(file_path):
    """Load sales data from CSV file"""
    df = pd.read_csv(file_path, encoding='latin1')
    print(f"Initial shape: {df.shape}")
    return df

# Step 1: Select required columns
def select_columns(df):
    """Keep only required columns"""
    required_cols = [
        'ORDERNUMBER', 'QUANTITYORDERED', 'PRICEEACH',
        'ORDERLINENUMBER', 'SALES', 'ORDERDATE', 
        'STATUS', 'QTR_ID', 'MONTH_ID', 'YEAR_ID'
    ]
    
    # Check if columns exist
    available_cols = [col for col in required_cols if col in df.columns]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
    
    df = df[available_cols].copy()
    print(f"Shape after column selection: {df.shape}")
    return df

# Step 2: Handle missing data
def handle_missing_data(df):
    """Handle missing values"""
    print("\nMissing values before handling:")
    print(df.isnull().sum())
    
    # Fill numeric columns with median
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
    
    # Fill categorical columns with mode
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].mode()[0], inplace=True)
    
    print("\nMissing values after handling:")
    print(df.isnull().sum())
    return df

# Step 3: Handle duplicates
def handle_duplicates(df):
    """Remove duplicate rows"""
    initial_count = len(df)
    df = df.drop_duplicates()
    removed_count = initial_count - len(df)
    print(f"\nRemoved {removed_count} duplicate rows")
    return df

# Step 4: Normalize categories
def normalize_categories(df):
    """Normalize categorical columns"""
    if 'STATUS' in df.columns:
        df['STATUS'] = df['STATUS'].str.strip().str.upper()
    
    print("\nUnique STATUS values:", df['STATUS'].unique())
    return df

# Step 5: Extract date components
def extract_date_features(df):
    """Extract Year, Month, Quarter from ORDERDATE"""
    if 'ORDERDATE' in df.columns:
        # Convert to datetime
        df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
        
        # Extract components if not already present
        if 'YEAR_ID' not in df.columns:
            df['YEAR_ID'] = df['ORDERDATE'].dt.year
        
        if 'MONTH_ID' not in df.columns:
            df['MONTH_ID'] = df['ORDERDATE'].dt.month
        
        if 'QTR_ID' not in df.columns:
            df['QTR_ID'] = df['ORDERDATE'].dt.quarter
    
    return df

# Step 6: Data validation
def validate_data(df):
    """Validate data quality"""
    print("\n=== Data Validation ===")
    print(f"Total rows: {len(df)}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nBasic statistics:\n{df.describe()}")
    
    # Check for negative values in important columns
    if 'SALES' in df.columns:
        negative_sales = df[df['SALES'] < 0]
        if len(negative_sales) > 0:
            print(f"\nWarning: {len(negative_sales)} rows with negative SALES")
    
    return df

# Step 7: Store in SQLite database
def store_in_database(df, db_path='sales_data.db'):
    """Store processed data in SQLite database"""
    conn = sqlite3.connect(db_path)
    
    # Store main sales data
    df.to_sql('sales', conn, if_exists='replace', index=False)
    
    # Create indices for faster queries
    cursor = conn.cursor()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orderdate ON sales(ORDERDATE)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON sales(STATUS)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON sales(YEAR_ID)')
    
    conn.commit()
    conn.close()
    print(f"\nData stored in {db_path}")

# Main preprocessing pipeline
def main(input_file, output_db='sales_data.db'):
    """Main preprocessing pipeline"""
    print("=== Starting Data Preprocessing ===\n")
    
    # Load data
    df = load_data(input_file)
    
    # Select columns
    df = select_columns(df)
    
    # Handle missing data
    df = handle_missing_data(df)
    
    # Handle duplicates
    df = handle_duplicates(df)
    
    # Normalize categories
    df = normalize_categories(df)
    
    # Extract date features
    df = extract_date_features(df)
    
    # Validate data
    df = validate_data(df)
    
    # Store in database
    store_in_database(df, output_db)
    
    # Save processed CSV
    output_csv = 'processed_sales_data.csv'
    df.to_csv(output_csv, index=False)
    print(f"\nProcessed data saved to {output_csv}")
    
    print("\n=== Preprocessing Complete ===")
    return df

# Usage
if __name__ == "__main__":
    # Replace with your actual file path
    input_file = 'sales_data.csv'
    df = main(input_file)