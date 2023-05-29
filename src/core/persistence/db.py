from alembic import command
from alembic.config import Config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def create_new_pg_session_maker(*, db_url: str) -> "sessionmaker[AsyncSession]":
    """Create database session factory from url."""
    engine = create_async_engine(url=db_url, future=True)
    async_session_maker = sessionmaker(bind=engine, future=True, class_=AsyncSession)
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
