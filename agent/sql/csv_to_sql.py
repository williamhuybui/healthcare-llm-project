import pandas as pd
import sqlite3
import os
from pathlib import Path

class CSVToSQLConverter:
    def __init__(self, raw_data_folder="data/raw", clean_data_folder="data/clean", file_name="healthcare.db"):
        self.raw_data_folder = Path(raw_data_folder)
        self.clean_data_folder = Path(clean_data_folder)
        self.db_path = os.path.join(clean_data_folder,file_name)
        self.conn = sqlite3.connect(self.db_path)
        
    def convert_all_csv_files(self):
        """Convert all CSV files in the data folder to SQL tables"""
        csv_files = list(self.raw_data_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"No CSV files found in {self.raw_data_folder}")
            return
            
        for csv_file in csv_files:
            table_name = csv_file.stem  # Use filename without extension as table name
            self.csv_to_sql(csv_file, table_name)
            
        print(f"Database created at: {self.db_path}")
        self.show_table_info()
        
    def csv_to_sql(self, csv_file, table_name):
        """Convert a single CSV file to SQL table"""
        try:
            df = pd.read_csv(csv_file)
            
            # Clean column names (remove spaces, special chars)
            df.columns = df.columns.str.replace(' ', '_').str.replace('[^A-Za-z0-9_]', '', regex=True)
            
            # Convert to SQL
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            print(f"[OK] Converted {csv_file.name} to table '{table_name}' ({len(df)} rows)")
            
        except Exception as e:
            print(f"[ERROR] Error converting {csv_file.name}: {e}")
            
    def show_table_info(self):
        """Display information about created tables"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
            
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    raw_data_folder = r"data/raw"
    clean_data_folder = r"data/clean"
    file_name = r"healthcare.db"
    converter = CSVToSQLConverter(raw_data_folder=raw_data_folder, clean_data_folder=clean_data_folder, file_name=file_name)
    try:
        converter.convert_all_csv_files()
    finally:
        converter.close()