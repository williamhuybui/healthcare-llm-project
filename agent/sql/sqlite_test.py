import sqlite3
import os

def show_all_tables(db_path):
    """Show all table names and their information in the SQLite database."""
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Database: {db_path}")
        print("=" * 60)
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print(f"Found {len(tables)} tables:\n")
        
        # Display each table with details
        for i, (table_name,) in enumerate(tables, 1):
            print(f"{i}. Table: {table_name}")
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            print(f"   Rows: {row_count:,}")
            print(f"   Columns ({len(columns)}):")
            
            for col_info in columns:
                col_name = col_info[1]
                col_type = col_info[2]
                not_null = "NOT NULL" if col_info[3] else ""
                default_val = f"DEFAULT {col_info[4]}" if col_info[4] else ""
                pk = "PRIMARY KEY" if col_info[5] else ""
                
                extras = " ".join(filter(None, [not_null, default_val, pk]))
                print(f"     - {col_name} ({col_type}) {extras}")
            
            print()  # Empty line between tables
        
        print("=" * 60)
        
        # Show just the table names for easy reference
        print("Table names only:")
        for table_name, in tables:
            print(f"  - {table_name}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {e}")


# Main execution
if __name__ == "__main__":
    # Try different possible database paths
    db_path ="data/clean/healthcare.db"
    # show_all_tables(db_path)

    query = "SELECT * FROM coverage LIMIT 5;"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        print(row)
