import sqlalchemy
from alembic import command
from alembic.config import Config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.lib.models import PgBaseModel


def create_new_pg_session_maker(*, db_url: str) -> async_sessionmaker[AsyncSession]:
    """Create database session factory from url."""
    engine = create_async_engine(url=db_url, future=True)
    async_session_maker = async_sessionmaker(bind=engine, future=True, expire_on_commit=False, autoflush=False)
    return async_session_maker


def create_new_test_pg_session_maker(*, db_url: str) -> async_sessionmaker[AsyncSession]:
    """Create test database session factory from url."""
    engine = create_async_engine(url=db_url, future=True, poolclass=pool.NullPool)
    async_session_maker = async_sessionmaker(bind=engine, future=True, expire_on_commit=False, autoflush=False)
    return async_session_maker


async def run_pg_migrations(*, db_url: str, migrations_path: str) -> None:
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", migrations_path)
    async_engine = create_async_engine(db_url, poolclass=pool.NullPool, future=True)

    def execute_upgrade(connection: Connection) -> None:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    async with async_engine.begin() as conn:
        await conn.run_sync(execute_upgrade)
    await async_engine.dispose()


async def clean_db(*, db_url: str) -> None:
    async_engine = create_async_engine(db_url, poolclass=pool.NullPool, future=True)
    meta = PgBaseModel.metadata
    async with async_engine.begin() as conn:
        for table in reversed(meta.sorted_tables):
            await conn.execute(
                sqlalchemy.text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;").execution_options(autocommit=True)
            )
        await conn.commit()
