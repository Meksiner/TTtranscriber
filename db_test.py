import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text  # 👈 добавляем это

DATABASE_URL = "postgresql+asyncpg://myuser:3489@localhost:5432/audio_db"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1;"))  # 👈 используем text()
        print("✅ Соединение успешно:", result.scalar())

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

