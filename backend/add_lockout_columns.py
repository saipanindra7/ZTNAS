#!/usr/bin/env python3
"""
Quick migration to add lockout columns to users table
"""

import psycopg2
from config.settings import settings
from sqlalchemy import create_engine

def add_lockout_columns():
    """Add missing lockout columns to users table"""
    
    print("Connecting to database...")
    try:
        # Parse the database URL
        db_url = settings.DATABASE_URL
        print(f"Database URL: {db_url.split('@')[0]}@***")
        
        # Create engine and get connection
        engine = create_engine(db_url)
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        # SQL commands to add columns
        commands = [
            # Add locked_until column (if not exists)
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;
            """,
            
            # Add failed_login_attempts column (if not exists)
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
            """,
            
            # Add last_locked_time column (if not exists)
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS last_locked_time TIMESTAMP;
            """,
            
            # Add lockout_count column (if not exists)
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS lockout_count INTEGER DEFAULT 0;
            """
        ]
        
        print("\nAdding missing columns to users table...")
        for i, cmd in enumerate(commands, 1):
            try:
                cursor.execute(cmd)
                print(f"✓ Command {i} executed")
            except Exception as e:
                print(f"⚠ Command {i}: {str(e)[:100]}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✓ Database migration completed successfully!")
        print("\nColumns added to users table:")
        print("  - locked_until (TIMESTAMP WITH TIME ZONE)")
        print("  - failed_login_attempts (INTEGER)")
        print("  - last_locked_time (TIMESTAMP)")
        print("  - lockout_count (INTEGER)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = add_lockout_columns()
    exit(0 if success else 1)
