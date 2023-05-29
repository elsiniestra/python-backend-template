import asyncio
import logging

from fastapi import FastAPI

from src.app import create_app
from src.core.config import MainSettings, create_settings
from src.core.persistence.db import run_pg_migrations
from src.core.persistence.redis import sync_redis_graph
from src.injected import AppEnvironment
from src.lib import errors, middlewares, providers, routers
from src.lib.logger import setup_logging
from src.lib.sentry import init_sentry_sdk

logger = logging.getLogger(__name__)


def api() -> FastAPI:
    logger.info("Starting app...")

    # Settings
    settings: MainSettings = create_settings()
    setup_logging(path=settings.config_path.logger)
    if settings.environment.is_production and settings.sentry.dsn:
        init_sentry_sdk(dsn=settings.sentry.dsn, traces_sample_rate=settings.sentry.traces_sample_rate)
    logger.debug(f"Config: {settings.dict()}")

    logger.debug("Running migrations...")
    asyncio.create_task(
        run_pg_migrations(
            db_url=settings.db.pg_connection_url,
            migrations_path=settings.db.migrations_path,
        )
    )
    asyncio.create_task(
        sync_redis_graph(
            connection_url=settings.redis.connection_url,
            graph_data_path=settings.redis.graph_data_path,
        )
    )
    logger.debug("Migrations ran successfully!")

    # Create app
    app: FastAPI = create_app(is_production=settings.environment.is_production)

    # Create Environment
    app_environment: AppEnvironment = AppEnvironment.create(
        db_url=settings.db.pg_connection_url,
        redis_url=settings.redis.connection_url,
        iam_graph_name=settings.redis.iam_graph_name,
        s3_region=settings.s3.region,
        s3_endpoint=settings.s3.endpoint,
        s3_access_key=settings.s3.access_key,
        s3_secret_key=settings.s3.secret_key,
    )

    # Setup routers
    routers.setup_routers(app=app, domain_holder=app_environment.domain_holder)

    # Setup middlewares
    middlewares.setup_middlewares(
        app=app,
        settings=settings,
    )

    # Setup providers
    providers.setup_providers(app=app, domain_holder=app_environment.domain_holder, settings=settings)

    # Setup exception handlers
    app.exception_handler(errors.AbstractError)(errors.global_exception_handler)

    return app
