import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('sqlite+aiosqlite:///./nexora.db')
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
        for row in result:
            print(row[0])
    await engine.dispose()

asyncio.run(check())