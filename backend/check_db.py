import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('sqlite+aiosqlite:///./nexora.db')
    async with engine.connect() as conn:
        result = await conn.execute(text('PRAGMA table_info(proposals)'))
        print('=== proposals table ===')
        for row in result:
            print(row)
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print('=== all tables ===')
        for row in result:
            print(row)
    await engine.dispose()

asyncio.run(check())