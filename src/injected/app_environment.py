from dataclasses import dataclass

from botocore.client import BaseClient as S3Client
from passlib.context import CryptContext
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core import persistence
from src.core.config import MainSettings, TestSettings
from src.injected import DomainHolder
from src.injected.sso_holder import SSOHolder


@dataclass(frozen=True)
class AppEnvironment:
    domain_holder: DomainHolder
    sso_holder: SSOHolder | None

    @classmethod
    def create(cls, *, settings: MainSettings) -> "AppEnvironment":
        pg_session_manager: async_sessionmaker[AsyncSession] = persistence.create_new_pg_session_maker(
            db_url=settings.db.pg_connection_url
        )
        redis_connection_pool: aioredis.ConnectionPool = persistence.create_redis_connection_pool(
            connection_url=settings.redis.connection_url
        )
        s3_client: S3Client = persistence.create_s3_client(
            region=settings.s3.region,
            endpoint=settings.s3.endpoint,
            access_key=settings.s3.access_key,
            secret_key=settings.s3.secret_key,
        )
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        domain_holder = DomainHolder.create(
            pg_session_manager=pg_session_manager,
            redis_connection_pool=redis_connection_pool,
            s3_client=s3_client,
            iam_graph_name=settings.redis.iam_graph_name,
            pwd_context=pwd_context,
        )
        sso_holder = SSOHolder.create(
            google_client_id=settings.sso.google.client_id,
            google_client_secret=settings.sso.google.client_secret,
            google_redirect_uri=settings.sso.google.redirect_uri,
            github_client_id=settings.sso.github.client_id,
            github_client_secret=settings.sso.github.client_secret,
            github_redirect_uri=settings.sso.github.redirect_uri,
            microsoft_client_id=settings.sso.microsoft.client_id,
            microsoft_client_secret=settings.sso.microsoft.client_secret,
            microsoft_redirect_uri=settings.sso.microsoft.redirect_uri,
            microsoft_tenant=settings.sso.microsoft.tenant,
        )
        return AppEnvironment(domain_holder=domain_holder, sso_holder=sso_holder)

    @classmethod
    def mock(cls, *, settings: TestSettings) -> "AppEnvironment":
        pg_session_manager: async_sessionmaker[AsyncSession] = persistence.create_new_test_pg_session_maker(
            db_url=settings.db.pg_connection_url
        )
        redis_connection_pool: aioredis.ConnectionPool = persistence.create_redis_connection_pool(
            connection_url=settings.redis.connection_url
        )
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        s3_client = persistence.create_s3_client(
            region="mocked",
            endpoint="mocked",
            access_key="mocked",
            secret_key="mocked",
        )
        domain_holder = DomainHolder.mock(
            pg_session_manager=pg_session_manager,
            redis_connection_pool=redis_connection_pool,
            iam_graph_name=settings.redis.iam_graph_name,
            pwd_context=pwd_context,
            s3_client=s3_client,
        )
        return AppEnvironment(domain_holder=domain_holder, sso_holder=None)
