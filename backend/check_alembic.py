from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio

async def check():
    engine = create_async_engine('sqlite+aiosqlite:///./nexora.db')
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT version_num FROM alembic_version'))
        print(result.fetchone())
    await engine.dispose()

asyncio.run(check())