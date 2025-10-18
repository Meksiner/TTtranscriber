import asyncio
import os
import sys
from typing import cast
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Добавляем путь к проекту, чтобы можно было импортировать app.*
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models import Base  # ✅ твои модели

# Alembic Config object
config = context.config

# Загружаем настройки логгера из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Метаданные для автогенерации миграций
target_metadata = Base.metadata

# URL базы данных (читаем из alembic.ini)
DATABASE_URL = cast(str, config.get_main_option("sqlalchemy.url"))

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)."""
    url = cast(str, config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Реальный запуск миграций в online-режиме."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Асинхронный запуск миграций."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


# Выбор режима запуска (offline / online)
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
