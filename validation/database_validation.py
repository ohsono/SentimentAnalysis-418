#!/usr/bin/env python3

"""
Database Validation Script
Tests database connectivity and functionality
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "worker"))

def test_database_config():
    """Test database configuration"""
    print("⚙️ Testing Database Configuration")
    print("-" * 40)
    
    try:
        from worker.config.worker_config import config
        db_config = config.get_database_config()
        
        required_fields = ['host', 'port', 'database', 'username', 'password']
        
        print(f"   🏠 Host: {db_config.get('host', 'NOT SET')}")
        print(f"   🔌 Port: {db_config.get('port', 'NOT SET')}")
        print(f"   💾 Database: {db_config.get('database', 'NOT SET')}")
        print(f"   👤 Username: {db_config.get('username', 'NOT SET')}")
        print(f"   🔐 Password: {'SET' if db_config.get('password') else 'NOT SET'}")
        
        missing_fields = [field for field in required_fields if not db_config.get(field)]
        
        if missing_fields:
            print(f"   ❌ Missing configuration: {missing_fields}")
            return False, f"Missing: {missing_fields}"
        
        print("   ✅ Database configuration complete")
        return True, db_config
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False, str(e)

def test_psycopg2_import():
    """Test PostgreSQL driver import"""
    print("\n📦 Testing PostgreSQL Driver")
    print("-" * 40)
    
    try:
        import psycopg2
        import psycopg2.extras
        
        version = psycopg2.__version__
        print(f"   ✅ psycopg2 imported successfully")
        print(f"   📋 Version: {version}")
        
        return True, version
        
    except ImportError as e:
        print(f"   ❌ psycopg2 not available: {e}")
        print("   💡 Install with: pip install psycopg2-binary")
        return False, str(e)

def test_database_connection():
    """Test actual database connection"""
    print("\n🔌 Testing Database Connection")
    print("-" * 40)
    
    try:
        import psycopg2
        from worker.config.worker_config import config
        
        db_config = config.get_database_config()
        
        print(f"   🔗 Connecting to {db_config['host']}:{db_config['port']}")
        print(f"   💾 Database: {db_config['database']}")
        
        # Create connection
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['username'],
            password=db_config['password'],
            connect_timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version_info = cursor.fetchone()[0]
        
        # Get basic database info
        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
        db_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"   ✅ Connection successful!")
        print(f"   📊 PostgreSQL Version: {version_info.split(',')[0]}")
        print(f"   💾 Current Database: {db_info[0]}")
        print(f"   👤 Current User: {db_info[1]}")
        print(f"   🌐 Server: {db_info[2]}:{db_info[3]}")
        
        return True, {
            'version': version_info,
            'database': db_info[0],
            'user': db_info[1],
            'server': f"{db_info[2]}:{db_info[3]}"
        }
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False, str(e)

def test_database_tables():
    """Test database tables and schema"""
    print("\n📋 Testing Database Schema")
    print("-" * 40)
    
    try:
        import psycopg2
        from worker.config.worker_config import config
        
        db_config = config.get_database_config()
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['username'],
            password=db_config['password']
        )
        
        cursor = conn.cursor()
        
        # Check for expected tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"      📄 {table}")
        
        # Check for sentiment-related tables
        expected_tables = ['posts', 'comments', 'sentiment_analysis', 'subreddits']
        found_expected = [table for table in expected_tables if table in tables]
        missing_expected = [table for table in expected_tables if table not in tables]
        
        if found_expected:
            print(f"   ✅ Expected tables found: {found_expected}")
        
        if missing_expected:
            print(f"   ⚠️ Expected tables missing: {missing_expected}")
        
        # Test a simple query on an existing table
        if tables:
            test_table = tables[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {test_table};")
                count = cursor.fetchone()[0]
                print(f"   📊 {test_table}: {count:,} rows")
            except Exception as e:
                print(f"   ⚠️ Could not query {test_table}: {e}")
        
        cursor.close()
        conn.close()
        
        return True, {
            'total_tables': len(tables),
            'tables': tables,
            'expected_found': found_expected,
            'expected_missing': missing_expected
        }
        
    except Exception as e:
        print(f"   ❌ Schema check failed: {e}")
        return False, str(e)

def test_database_manager():
    """Test DatabaseManager class if available"""
    print("\n🔧 Testing Database Manager")
    print("-" * 40)
    
    try:
        from app.database.postgres_manager import DatabaseManager, POSTGRES_AVAILABLE
        
        if not POSTGRES_AVAILABLE:
            print("   ⚠️ DatabaseManager reports PostgreSQL not available")
            return False, "PostgreSQL not available according to manager"
        
        print("   📦 DatabaseManager imported successfully")
        
        # Try to create instance
        db_manager = DatabaseManager()
        print("   ✅ DatabaseManager instantiated")
        
        # Test initialization (async)
        import asyncio
        
        async def test_init():
            try:
                await db_manager.initialize()
                print("   ✅ DatabaseManager initialized successfully")
                
                # Test basic functionality
                await db_manager.close()
                print("   ✅ DatabaseManager closed successfully")
                
                return True, "DatabaseManager working"
                
            except Exception as e:
                print(f"   ❌ DatabaseManager initialization failed: {e}")
                return False, str(e)
        
        # Run async test
        result = asyncio.run(test_init())
        return result
        
    except ImportError as e:
        print(f"   ⚠️ DatabaseManager not available: {e}")
        return False, f"Import error: {e}"
    except Exception as e:
        print(f"   ❌ DatabaseManager test failed: {e}")
        return False, str(e)

def test_database_operations():
    """Test basic database operations"""
    print("\n💽 Testing Database Operations")
    print("-" * 40)
    
    try:
        import psycopg2
        import psycopg2.extras
        from worker.config.worker_config import config
        
        db_config = config.get_database_config()
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['username'],
            password=db_config['password']
        )
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Test 1: Create temporary table
        print("   🔧 Creating temporary test table...")
        cursor.execute("""
            CREATE TEMP TABLE test_validation (
                id SERIAL PRIMARY KEY,
                test_text VARCHAR(100),
                test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Test 2: Insert data
        print("   ➕ Inserting test data...")
        cursor.execute("""
            INSERT INTO test_validation (test_text) 
            VALUES ('Validation Test') 
            RETURNING id, test_timestamp;
        """)
        
        inserted = cursor.fetchone()
        print(f"      📝 Inserted record ID: {inserted['id']}")
        
        # Test 3: Query data
        print("   🔍 Querying test data...")
        cursor.execute("SELECT * FROM test_validation;")
        results = cursor.fetchall()
        
        print(f"   ✅ Database operations successful!")
        print(f"      📊 Records found: {len(results)}")
        
        # Test 4: Transaction rollback (cleanup)
        conn.rollback()  # This will remove the temp table
        
        cursor.close()
        conn.close()
        
        return True, f"Operations successful, {len(results)} records processed"
        
    except Exception as e:
        print(f"   ❌ Database operations failed: {e}")
        return False, str(e)

def main():
    """Main validation function"""
    print("💾 Database Validation")
    print("=" * 60)
    print(f"📁 Project Root: {project_root}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Configuration
    config_success, config_msg = test_database_config()
    results.append(("Configuration", config_success, config_msg))
    
    if not config_success:
        print("\n❌ Cannot proceed without valid database configuration")
        print("💡 Configure PostgreSQL settings in .env.scheduler")
        print_summary(results)
        return
    
    # Test 2: Driver Import
    driver_success, driver_msg = test_psycopg2_import()
    results.append(("PostgreSQL Driver", driver_success, driver_msg))
    
    if not driver_success:
        print("\n❌ Cannot proceed without PostgreSQL driver")
        print_summary(results)
        return
    
    # Test 3: Connection
    conn_success, conn_msg = test_database_connection()
    results.append(("Database Connection", conn_success, conn_msg))
    
    if not conn_success:
        print("\n❌ Cannot proceed without database connection")
        print("💡 Check database server status and configuration")
        print_summary(results)
        return
    
    # Test 4: Schema
    schema_success, schema_msg = test_database_tables()
    results.append(("Database Schema", schema_success, schema_msg))
    
    # Test 5: Database Manager
    manager_success, manager_msg = test_database_manager()
    results.append(("Database Manager", manager_success, manager_msg))
    
    # Test 6: Operations
    ops_success, ops_msg = test_database_operations()
    results.append(("Database Operations", ops_success, ops_msg))
    
    # Summary
    print_summary(results)

def print_summary(results):
    """Print validation summary"""
    print("\n" + "=" * 60)
    print("📊 DATABASE VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = len([r for r in results if r[1] is True])
    failed_tests = len([r for r in results if r[1] is False])
    
    print(f"📈 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if total_tests > 0:
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print("\n📋 Detailed Results:")
    for test_name, status, message in results:
        if status is True:
            print(f"   ✅ {test_name}: {message}")
        elif status is False:
            print(f"   ❌ {test_name}: {message}")
        else:
            print(f"   ⚠️ {test_name}: {message}")
    
    if failed_tests == 0 and passed_tests > 0:
        print("\n🎉 Database validation successful!")
        print("🚀 Database is ready for the pipeline service")
    elif failed_tests > 0:
        print(f"\n⚠️ Database validation completed with {failed_tests} issues")
        print("\n💡 Common solutions:")
        print("   • Check PostgreSQL server is running")
        print("   • Verify connection details in .env.scheduler")
        print("   • Ensure database and user exist")
        print("   • Check firewall/network access")
    
    print("\n💡 Next steps:")
    print("   • Test Reddit scraper: python validation/reddit_scraper_validation.py")
    print("   • Run full validation: python validation/comprehensive_validation.py")

if __name__ == "__main__":
    main()
