import sqlite3
import os

# Find the database file
db_file = "./fraud_detection.db"
if not os.path.exists(db_file):
    print(f"Database file not found at {os.path.abspath(db_file)}")
    # Try to find it in other locations
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db"):
                print(f"Found database file: {os.path.join(root, file)}")

# Connect to the database if it exists
if os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Show schema for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"  Columns in {table[0]}:")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
        
        # Count rows in each table
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")
        
        # Show a sample of data if there are rows
        if count > 0:
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
            rows = cursor.fetchall()
            print(f"  Sample data:")
            for row in rows:
                print(f"    {row}")
        
        print()
    
    conn.close()
else:
    print("No database file found to connect to.")
