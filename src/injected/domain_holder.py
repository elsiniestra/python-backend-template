from dataclasses import dataclass

from botocore.client import BaseClient as S3Client
from passlib.context import CryptContext
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domains import (
    ArticleDomain,
    ImageDomain,
    OauthDomain,
    UserDomain,
    create_article_domain,
    create_image_domain,
    create_oauth_domain,
    create_user_domain,
)


@dataclass(frozen=True)
class DomainHolder:
    oauth: OauthDomain
    image: ImageDomain
    user: UserDomain
    article: ArticleDomain

    @classmethod
    def create(
        cls,
        *,
        pg_session_manager: "sessionmaker[AsyncSession]",
        redis_connection_pool: aioredis.ConnectionPool,
        s3_client: S3Client,
        iam_graph_name: str,
        pwd_context: CryptContext,
    ) -> "DomainHolder":
        return DomainHolder(
            oauth=create_oauth_domain(
                pg_session_manager=pg_session_manager,
                redis_connection_pool=redis_connection_pool,
                iam_graph_name=iam_graph_name,
                pwd_context=pwd_context,
            ),
            image=create_image_domain(s3_client=s3_client),
            user=create_user_domain(
                pg_session_manager=pg_session_manager,
                redis_connection_pool=redis_connection_pool,
                iam_graph_name=iam_graph_name,
                pwd_context=pwd_context,
            ),
            article=create_article_domain(pg_session_manager=pg_session_manager),
        )
