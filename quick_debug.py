#!/usr/bin/env python3

"""
Quick debug script to identify the exact database issue
"""

import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ dotenv loaded")
except ImportError:
    print("❌ python-dotenv not installed")

# Check environment variables
print("\n📊 Environment Variables:")
db_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
for var in db_vars:
    value = os.getenv(var)
    print(f"  {var}: {'✅ ' + str(value) if value else '❌ Missing'}")

# Check Python packages
print("\n📦 Python Dependencies:")
try:
    import asyncpg
    print("  ✅ asyncpg installed")
except ImportError as e:
    print(f"  ❌ asyncpg not installed: {e}")

try:
    import sqlalchemy
    print("  ✅ sqlalchemy installed")
except ImportError as e:
    print(f"  ❌ sqlalchemy not installed: {e}")

# Test basic asyncpg connection
print("\n🔌 Testing Basic Connection:")
try:
    import asyncio
    import asyncpg
    
    async def test_connection():
        try:
            conn = await asyncpg.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'sentiment_db'),
                user=os.getenv('POSTGRES_USER', 'sentiment_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'sentiment_password')
            )
            print("  ✅ Basic asyncpg connection successful!")
            
            # Test simple query
            result = await conn.fetchval('SELECT 1')
            print(f"  ✅ Query test: {result}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False
    
    # Run the test
    success = asyncio.run(test_connection())
    
    if success:
        print("\n✅ Basic connection works! The issue is probably with the DatabaseManager class.")
    else:
        print("\n❌ Basic connection failed. Check PostgreSQL setup.")
        
except Exception as e:
    print(f"  ❌ Cannot test connection: {e}")

print("\n💡 Next steps:")
print("  1. If asyncpg is missing: pip install asyncpg")
print("  2. If env vars are missing: check your .env file")
print("  3. If basic connection fails: check PostgreSQL is running")
print("  4. If basic connection works: the issue is with DatabaseManager")
