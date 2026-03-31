#!/usr/bin/env python3
"""
Database Migration: Add Account Lockout Fields
March 29, 2026

This migration adds the new fields required for the account lockout system:
- locked_until (DateTime) - When the account lockout expires
- lockout_count (Integer) - How many times the account has been locked

Run this before deploying Phase 1 enterprise security features.
"""

from sqlalchemy import Column, DateTime, Integer
from datetime import datetime
import sys

def create_migration_script():
    """Generate raw SQL migration script"""
    
    sql_statements = [
        # Add locked_until column if it doesn't exist
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL;
        """,
        
        # Add lockout_count column if it doesn't exist
        """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_count INTEGER DEFAULT 0;
        """,
        
        # Create index on locked_until for faster lookups
        """
        CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
        """,
        
        # Create index on is_locked for faster queries
        """
        CREATE INDEX IF NOT EXISTS idx_users_is_locked ON users(is_locked);
        """
    ]
    
    return sql_statements

def print_migration_sql():
    """Print the migration SQL statements"""
    print("=" * 70)
    print("DATABASE MIGRATION: Account Lockout Fields")
    print("=" * 70)
    print()
    print("Run these SQL statements against your PostgreSQL database:")
    print()
    
    for i, statement in enumerate(create_migration_script(), 1):
        print(f"-- Statement {i}")
        print(statement.strip())
        print()

def generate_alembic_migration():
    """Generate Alembic migration file content"""
    
    migration_content = '''"""Account Lockout System - Add Fields

Revision ID: 001_add_account_lockout_fields
Revises: <previous_revision>
Create Date: 2026-03-29 10:30:00.000000

Adds fields required for the account lockout system:
- locked_until: DateTime when lockout expires
- lockout_count: Track how many times account has been locked
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_account_lockout_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration"""
    # Add locked_until column
    op.add_column('users', sa.Column(
        'locked_until',
        sa.DateTime(timezone=True),
        nullable=True
    ))
    
    # Add lockout_count column
    op.add_column('users', sa.Column(
        'lockout_count',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))
    
    # Create indexes for performance
    op.create_index(
        'idx_users_locked_until',
        'users',
        ['locked_until']
    )
    
    op.create_index(
        'idx_users_is_locked',
        'users',
        ['is_locked']
    )


def downgrade() -> None:
    """Revert migration"""
    # Drop indexes
    op.drop_index('idx_users_is_locked', table_name='users')
    op.drop_index('idx_users_locked_until', table_name='users')
    
    # Drop columns
    op.drop_column('users', 'lockout_count')
    op.drop_column('users', 'locked_until')
'''
    
    return migration_content

def print_deployment_instructions():
    """Print step-by-step deployment instructions"""
    
    instructions = """
DEPLOYMENT INSTRUCTIONS
========================

Option 1: Using Alembic (Recommended)
======================================

1. Create migration file:
   cd backend
   alembic revision --autogenerate -m "Add account lockout fields"

2. Edit the generated migration file and verify it contains:
   - ALTER TABLE users ADD COLUMN locked_until ...
   - ALTER TABLE users ADD COLUMN lockout_count ...
   - CREATE INDEX idx_users_locked_until ...
   - CREATE INDEX idx_users_is_locked ...

3. Apply migration:
   alembic upgrade head

4. Verify migration applied:
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'users' 
   AND column_name IN ('locked_until', 'lockout_count');


Option 2: Direct SQL (Development/Testing)
===========================================

1. Connect to your PostgreSQL database:
   psql -U postgres -d ztnas_db

2. Run the statements below:
   
   -- Add locked_until column
   ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL;
   
   -- Add lockout_count column  
   ALTER TABLE users ADD COLUMN IF NOT EXISTS lockout_count INTEGER DEFAULT 0;
   
   -- Create indexes
   CREATE INDEX IF NOT EXISTS idx_users_locked_until ON users(locked_until);
   CREATE INDEX IF NOT EXISTS idx_users_is_locked ON users(is_locked);

3. Verify:
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'users';


Option 3: Using Python Alembic CLI
===================================

1. Install alembic if not already installed:
   pip install alembic

2. Initialize migrations (if not already done):
   cd backend
   alembic init migrations

3. Edit migrations/env.py to set up database connection

4. Create migration:
   alembic revision --autogenerate -m "Add account lockout fields"

5. Review the generated file in migrations/versions/

6. Apply migration:
   alembic upgrade head

7. Verify:
   alembic history  # Show all migrations
   alembic current  # Show current version


Pre-Deployment Verification
============================

1. Backup your database:
   pg_dump -U postgres ztnas_db > backup_2026-03-29.sql.gz

2. Test migration on staging first:
   - Copy production database to staging
   - Apply migration to staging
   - Run test suite
   - Verify no errors in logs

3. Check database after migration:
   """
    
    print(instructions)
    
    # Print verification SQL
    print("   SELECT table_name, column_name, data_type, is_nullable")
    print("   FROM information_schema.columns")
    print("   WHERE table_name = 'users'")
    print("   ORDER BY ordinal_position;")
    
    print("""

4. Monitor after deployment:
   - Watch application logs for schema errors
   - Verify no 500 errors in auth endpoints
   - Test account lockout functionality

5. Rollback procedure (if needed):
   alembic downgrade -1  # Go back one migration
   OR
   ALTER TABLE users DROP COLUMN locked_until, DROP COLUMN lockout_count;


Post-Deployment Verification
=============================

1. Test account lockout system:
   python backend/tests/test_enterprise_security.py

2. Check for newly locked/unlocked accounts:
   SELECT id, username, is_locked, locked_until, failed_login_attempts
   FROM users
   WHERE is_locked = true;

3. Verify indexes were created:
   SELECT indexname FROM pg_stat_indexes WHERE tablename = 'users';
   -- Should show idx_users_locked_until and idx_users_is_locked

4. Monitor performance:
   SELECT COUNT(*) FROM users WHERE is_locked = true;  # Should be fast
   SELECT * FROM users WHERE locked_until > NOW();     # Should be fast


Troubleshooting
===============

Issue: "Column already exists" error
Solution: Your database already has the columns. Check if you're 
re-running the migration. If upgrading from previous version, 
verify columns exist with the SELECT query above.

Issue: Permission denied when running SQL
Solution: Make sure you're using a database user with ALTER permissions.
For production, use dedicated migration user with appropriate privileges.

Issue: Migration hangs
Solution: Check if there are long-running queries blocking the migration.
Kill them with: SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE usename = 'user_name';

Issue: Performance problems after migration
Solution: Run ANALYZE to update query planner statistics:
   ANALYZE users;
   ANALYZE;  -- Full database


Rollback Procedure
==================

If you need to rollback the migration:

Using Alembic:
   alembic downgrade -1  # Go back one migration

Manual SQL:
   ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
   ALTER TABLE users DROP COLUMN IF EXISTS lockout_count;
   DROP INDEX IF EXISTS idx_users_locked_until;
   DROP INDEX IF EXISTS idx_users_is_locked;
   
   # Restart application after rollback
"""
    )

def main():
    print()
    print_migration_sql()
    print()
    print_deployment_instructions()
    print()
    print("=" * 70)
    print("Migration ready! Follow the options above to deploy.")
    print("=" * 70)
    print()

if __name__ == "__main__":
    main()
