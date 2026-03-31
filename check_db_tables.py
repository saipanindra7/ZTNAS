#!/usr/bin/env python3
"""Check database schema for existing tables"""

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print('📊 Existing tables in database:\n')
    for i, table in enumerate(tables, 1):
        print(f'{i}. {table["table_name"]}')
        
        # Get columns for each table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table['table_name'],))
        
        columns = cursor.fetchall()
        for col in columns:
            print(f'   - {col["column_name"]}: {col["data_type"]}')
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
