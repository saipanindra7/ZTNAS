#!/usr/bin/env python3
"""
Check database schema and tables
"""

import sqlite3

db_path = 'd:\\projects\\ztnas\\backend\\test.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Database Tables:\n")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("  ❌ No tables found!")
    else:
        for table_name in tables:
            table = table_name[0]
            print(f"\n  📋 Table: {table}")
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                col_id, col_name, col_type, notnull, default, pk = col
                print(f"      • {col_name}: {col_type}")
    
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
