import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # добавляет корень проекта

from app.models import Base

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.models import Base  # твои модели

# Alembic Config object
config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

# создаём движок для асинхронных подключений
DATABASE_URL = config.get_main_option("sqlalchemy.url")
engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
