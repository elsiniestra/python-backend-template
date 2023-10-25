import asyncio

from src.core.config import TestSettings, create_test_settings
from src.core.persistence import db, redis
from src.injected import AppEnvironment
from src.tests.fixtures.load_articles import load_articles
from src.tests.fixtures.load_users import load_users


async def load_fixtures(settings: TestSettings) -> None:
    domain_holder = AppEnvironment.mock(settings=settings).domain_holder

    await load_users(domain_holder)
    await load_articles(domain_holder, settings=settings)


if __name__ == "__main__":
    settings = create_test_settings()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        db.run_pg_migrations(db_url=settings.db.pg_connection_url, migrations_path=settings.db.migrations_path)
    )
    loop.run_until_complete(
        redis.sync_redis_graph(
            connection_url=settings.redis.connection_url,
            graph_data_path=settings.redis.graph_data_path,
        )
    )
    loop.run_until_complete(db.clean_db(db_url=settings.db.pg_connection_url))
    loop.run_until_complete(
        load_fixtures(
            settings=settings,
        )
    )
