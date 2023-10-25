import asyncio
import logging

from fastapi import FastAPI

from src.app import create_app
from src.core import config, persistence
from src.injected import AppEnvironment
from src.lib import errors
from src.lib import logger as logger_pkg
from src.lib import middlewares, providers, routers, sentry

logger = logging.getLogger(__name__)


def api() -> FastAPI:
    logger.info("Starting app...")

    # Settings
    settings: config.MainSettings = config.create_settings()
    logger_pkg.setup_logging(path=settings.config_path.logger)
    if settings.environment.is_production and settings.sentry.dsn:
        sentry.init_sentry_sdk(dsn=settings.sentry.dsn, traces_sample_rate=settings.sentry.traces_sample_rate)
    logger.debug(f"Config: {settings.model_dump()}")

    logger.debug("Running migrations...")
    asyncio.create_task(
        persistence.run_pg_migrations(
            db_url=settings.db.pg_connection_url,
            migrations_path=settings.db.migrations_path,
        )
    )
    asyncio.create_task(
        persistence.sync_redis_graph(
            connection_url=settings.redis.connection_url,
            graph_data_path=settings.redis.graph_data_path,
        )
    )
    logger.debug("Migrations ran successfully!")

    # Create app
    app: FastAPI = create_app(is_production=settings.environment.is_production)

    # Create Environment
    app_environment: AppEnvironment = AppEnvironment.create(settings=settings)

    # Setup routers
    routers.setup_routers(app=app, domain_holder=app_environment.domain_holder)

    # Setup middlewares
    middlewares.setup_middlewares(
        app=app,
        settings=settings,
    )

    # Setup providers
    providers.setup_providers(
        app=app, domain_holder=app_environment.domain_holder, sso_holder=app_environment.sso_holder, settings=settings
    )

    # Setup exception handlers
    app.exception_handler(errors.AbstractError)(errors.global_exception_handler)

    return app
