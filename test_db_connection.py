#!/usr/bin/env python3
"""
Test database connection
"""
import os
import asyncio
import asyncpg

async def test_connection():
    print("Testing PostgreSQL connection...")
    print(f"Host: {os.environ.get('PGHOST', 'localhost')}")
    print(f"Port: {os.environ.get('PGPORT', '5432')}")
    print(f"User: {os.environ.get('PGUSER', 'postgres')}")
    print(f"Database: {os.environ.get('PGDATABASE', 'studentperformancedb')}")
    
    try:
        conn = await asyncpg.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            port=int(os.environ.get('PGPORT', '5432')),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', ''),
            database=os.environ.get('PGDATABASE', 'studentperformancedb')
        )
        
        result = await conn.fetchval('SELECT version()')
        print(f"\n✓ Connection successful!")
        print(f"PostgreSQL version: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == '__main__':
    asyncio.run(test_connection())
