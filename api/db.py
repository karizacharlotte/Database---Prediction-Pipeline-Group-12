"""
FastAPI Database Helper using asyncpg for PostgreSQL connections
"""
import os
import asyncpg

POOL = None

def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.environ.get('PGHOST', 'localhost'),
        'port': int(os.environ.get('PGPORT', 5432)),
        'user': os.environ.get('PGUSER', 'postgres'),
        'password': os.environ.get('PGPASSWORD', ''),
        'database': os.environ.get('PGDATABASE', 'studentperformancedb')
    }

async def connect():
    """Create and return connection pool"""
    global POOL
    if POOL is None:
        POOL = await asyncpg.create_pool(**get_db_config())
    return POOL

async def close():
    """Close connection pool"""
    global POOL
    if POOL is not None:
        await POOL.close()
        POOL = None

async def fetchrow(query, *args):
    """Fetch single row"""
    pool = await connect()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)

async def fetch(query, *args):
    """Fetch multiple rows"""
    pool = await connect()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute(query, *args):
    """Execute query without return"""
    pool = await connect()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)
