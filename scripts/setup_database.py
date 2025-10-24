#!/usr/bin/env python3
"""
Database Setup Script for RA-D-PS Parse Case Management
Creates tables and optionally seeds with initial data
"""

import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ra_d_ps.database import ParseCaseRepository, db_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_database():
    """
    Setup PostgreSQL database for parse case management
    """
    print("=" * 60)
    print("RA-D-PS Parse Case Database Setup")
    print("=" * 60)
    
    # Display configuration
    print(f"\n📊 Database Configuration:")
    print(f"   Host: {db_config.postgresql.host}")
    print(f"   Port: {db_config.postgresql.port}")
    print(f"   Database: {db_config.postgresql.database}")
    print(f"   User: {db_config.postgresql.user}")
    print(f"   SSL Mode: {db_config.postgresql.ssl_mode}")
    print(f"   Pool Size: {db_config.postgresql.pool_size}")
    
    # Confirm before proceeding
    response = input("\n⚠️  This will create database tables. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Setup cancelled.")
        return
    
    try:
        print("\n🔧 Initializing repository...")
        repo = ParseCaseRepository()
        
        print("🔧 Creating database tables...")
        repo.create_tables()
        
        print("\n✅ Database setup complete!")
        print("\nNext steps:")
        print("1. Run: python scripts/seed_parse_cases.py (to add parse case data)")
        print("2. Verify: psql -h localhost -U ra_d_ps_user -d ra_d_ps -c '\\dt'")
        
        repo.close()
        
    except Exception as e:
        logger.error(f"Failed to setup database: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running: pg_ctl status")
        print("2. Create database: createdb -U postgres ra_d_ps")
        print("3. Create user: createuser -U postgres ra_d_ps_user")
        print("4. Grant privileges: psql -U postgres -c 'GRANT ALL ON DATABASE ra_d_ps TO ra_d_ps_user;'")
        print("5. Check .env file has correct DB_PASSWORD")
        sys.exit(1)


def reset_database():
    """
    Drop and recreate all tables (DESTRUCTIVE!)
    """
    print("=" * 60)
    print("⚠️  WARNING: DATABASE RESET")
    print("=" * 60)
    print("\nThis will DELETE ALL DATA and recreate tables.")
    
    response = input("Type 'RESET' to confirm: ")
    if response != 'RESET':
        print("❌ Reset cancelled.")
        return
    
    try:
        repo = ParseCaseRepository()
        
        print("\n🗑️  Dropping all tables...")
        repo.drop_tables()
        
        print("🔧 Recreating tables...")
        repo.create_tables()
        
        print("\n✅ Database reset complete!")
        repo.close()
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def test_connection():
    """
    Test database connection
    """
    print("=" * 60)
    print("Testing PostgreSQL Connection")
    print("=" * 60)
    
    try:
        print("\n🔌 Connecting to database...")
        repo = ParseCaseRepository()
        
        with repo.get_session() as session:
            result = session.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n✅ Connection successful!")
            print(f"   PostgreSQL version: {version}")
        
        repo.close()
        
    except Exception as e:
        logger.error(f"Connection failed: {e}", exc_info=True)
        print(f"\n❌ Connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RA-D-PS Database Setup")
    parser.add_argument(
        'action',
        choices=['setup', 'reset', 'test'],
        help='Action to perform: setup (create tables), reset (drop and recreate), test (test connection)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'setup':
        setup_database()
    elif args.action == 'reset':
        reset_database()
    elif args.action == 'test':
        test_connection()
