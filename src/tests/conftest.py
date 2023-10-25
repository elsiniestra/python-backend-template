import asyncio
from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from redis import asyncio as aioredis
from starlette.testclient import TestClient

from src.app import create_app
from src.core.config import TestSettings, create_test_settings
from src.core.persistence import redis
from src.injected import AppEnvironment
from src.lib import errors, middlewares, providers, routers, schemas, utils


@pytest.fixture(scope="module")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def settings() -> TestSettings:
    return create_test_settings()


@pytest.fixture(scope="module")
def testuser() -> schemas.User:
    return schemas.User(id=1, first_name="Test", last_name="Test", username="testuser", email="user@test.com")


@pytest.fixture(scope="module")
def admin() -> schemas.User:
    return schemas.User(id=2, first_name="Admin", last_name="Admin", username="admin", email="admin@admin.com")


@pytest.fixture(scope="module")
def admin_tokens() -> schemas.RotateTokenResponse:
    return schemas.RotateTokenResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQwODcxNTIxODksInN1YiI6IjIiLCJpcnQiOmZhbHNlfQ.bd8561o9gJu3XPd3dhumjxmTQ0jE5U-05dbitYs2xfQ",  # noqa
        access_token_expires_at=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQwODcxNTIxODksInN1YiI6IjIiLCJpcnQiOnRydWV9.I72d2gJkvJZZ593bxJya-QqR6NeBPCbAu2y-Iu-W0HY",  # noqa
        refresh_token_expires_at=int((datetime.utcnow() + timedelta(days=2)).timestamp()),
    )


@pytest.fixture(scope="module")
def user_tokens() -> schemas.RotateTokenResponse:
    return schemas.RotateTokenResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQwODcxNTIxODksInN1YiI6IjEiLCJpcnQiOmZhbHNlfQ.WmKYP58N_QJYrNeFg39ia25i4NUv6oTW7Bmv1pdqZ40",  # noqa
        access_token_expires_at=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQwODcxNTIxODksInN1YiI6IjEiLCJpcnQiOnRydWV9.aDQY3WpBxoONpS0DiQ-CgKM9s8ws3yHk8DkAua15TXU",  # noqa
        refresh_token_expires_at=int((datetime.utcnow() + timedelta(days=2)).timestamp()),
    )


@pytest.fixture(scope="module")
def admin_auth_headers(admin_tokens) -> dict:
    return {"Authorization": f"Bearer {admin_tokens.access_token}"}


@pytest.fixture(scope="module")
def user_auth_headers(user_tokens) -> dict:
    return {"Authorization": f"Bearer {user_tokens.access_token}"}


@pytest.fixture(scope="module")
def expired_auth_headers(user_tokens) -> dict:
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNTE2MjM5MDIyLCJpcnQiOnRydWV9.TJ88YzriOV5nsQL2ssQsUCodbawH9fFD-axJhDxjTwY"  # noqa
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def wrong_sub_auth_headers(user_tokens) -> dict:
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTkiLCJleHAiOjQwODcxNTIxODksImlydCI6dHJ1ZX0.ZlfsszOQy6_KjwAnZw7VcJxboKKRrCwiK_d02u0GMbs"  # noqa
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client(settings) -> TestClient:
    app: FastAPI = create_app(is_production=settings.environment.is_production)
    app_environment = AppEnvironment.mock(settings=settings)
    routers.setup_routers(app=app, domain_holder=app_environment.domain_holder)
    middlewares.setup_middlewares(
        app=app,
        settings=settings,
    )
    providers.setup_providers(
        app=app, domain_holder=app_environment.domain_holder, sso_holder=app_environment.sso_holder, settings=settings
    )
    app.exception_handler(errors.AbstractError)(errors.global_exception_handler)

    return TestClient(app)


@pytest.fixture(scope="module", autouse=True)
async def autoload_refresh_token(redis_pipe, testuser, user_tokens):
    async with redis_pipe:
        await redis_pipe.sadd(testuser.id, user_tokens.refresh_token).execute()


@pytest.fixture(scope="module")
def redis_conn_pool(settings):
    return redis.create_redis_connection_pool(connection_url=settings.redis.connection_url)


@pytest.fixture(scope="module")
async def redis_session(redis_conn_pool):
    session: "aioredis.Redis[Any]" = aioredis.Redis(connection_pool=redis_conn_pool)
    try:
        async with session.client() as conn:
            yield conn
    finally:
        await session.close()


@pytest.fixture(scope="module")
async def redis_pipe(redis_session):
    async with redis_session.pipeline(transaction=True) as pipe:
        yield pipe


@pytest.fixture(scope="module")
def curr_timestamp():
    return utils.get_current_timestamp()


def clean_results(
    obj1,
    obj2,
    strip_fields=(
        "created_at",
        "updated_at",
    ),
):
    def _strip_fields(obj):
        for field in strip_fields:
            if field in obj:
                obj.pop(field)
        if "items" in obj:
            for item in obj["items"]:
                _strip_fields(item)

    _strip_fields(obj1)
    _strip_fields(obj2)
