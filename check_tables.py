#!/usr/bin/env python3

"""
Check what tables and columns actually exist in the database
"""

import os
import asyncio

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ python-dotenv not installed")

async def check_database_structure():
    """Check existing database structure"""
    print("🔍 CHECKING EXISTING DATABASE STRUCTURE")
    print("=" * 50)
    
    try:
        import asyncpg
        
        # Connect to database
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB', 'sentiment_db'),
            user=os.getenv('POSTGRES_USER', 'sentiment_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'sentiment_password')
        )
        print("✅ Connected to PostgreSQL")
        
        # Get list of tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  📄 {table['table_name']}")
        
        # Check each table's structure
        for table in tables:
            table_name = table['table_name']
            print(f"\n🔍 Structure of '{table_name}':")
            
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position
            """, table_name)
            
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  • {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Show sample data if any exists
        print(f"\n📊 Data counts:")
        for table in tables:
            table_name = table['table_name']
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"  📈 {table_name}: {count} rows")
                
                # Show sample data for first few rows
                if count > 0:
                    sample = await conn.fetch(f"SELECT * FROM {table_name} LIMIT 2")
                    print(f"    Sample: {len(sample[0] if sample else [])} columns")
            except Exception as e:
                print(f"  ❌ Error querying {table_name}: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_structure())
