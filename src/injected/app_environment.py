from dataclasses import dataclass

from botocore.client import BaseClient as S3Client
from passlib.context import CryptContext
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.persistence import create_new_pg_session_maker, create_s3_client
from src.core.persistence.redis import create_redis_connection_pool
from src.injected import DomainHolder


@dataclass(frozen=True)
class AppEnvironment:
    domain_holder: DomainHolder

    @classmethod
    def create(
        cls,
        *,
        db_url: str,
        redis_url: str,
        iam_graph_name: str,
        s3_region: str,
        s3_endpoint: str,
        s3_access_key: str,
        s3_secret_key: str,
    ) -> "AppEnvironment":
        pg_session_manager: "sessionmaker[AsyncSession]" = create_new_pg_session_maker(db_url=db_url)
        redis_connection_pool: aioredis.ConnectionPool = create_redis_connection_pool(connection_url=redis_url)
        s3_client: S3Client = create_s3_client(
            region=s3_region,
            endpoint=s3_endpoint,
            access_key=s3_access_key,
            secret_key=s3_secret_key,
        )
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        domain_holder = DomainHolder.create(
            pg_session_manager=pg_session_manager,
            redis_connection_pool=redis_connection_pool,
            s3_client=s3_client,
            iam_graph_name=iam_graph_name,
            pwd_context=pwd_context,
        )
        return AppEnvironment(domain_holder=domain_holder)
