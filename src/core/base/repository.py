import abc
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Generic, Self, TypeVar

from botocore.client import BaseClient as S3Client
from pydantic import BaseModel as PydanticBaseModel
from redis import asyncio as aioredis
from redis.asyncio.client import Pipeline as RedisPipeline
from redis.commands.graph import Graph
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.lib import errors, models, pagination, schemas
from src.lib.schemas import BaseModelWithCount as PydanticBaseModelWithCount

DBModelType = TypeVar("DBModelType", bound=models.PgBaseModel)
PydanticModelType = TypeVar("PydanticModelType", bound=PydanticBaseModel)
# python does not support generic typevars, so we silence the error with "type: ignore"
PydanticModelWithCountType = TypeVar("PydanticModelWithCountType", bound=PydanticBaseModelWithCount)  # type: ignore
PydanticModelCreateType = TypeVar("PydanticModelCreateType", bound=PydanticBaseModel)
PydanticModelUpdateType = TypeVar("PydanticModelUpdateType", bound=PydanticBaseModel)


class BaseRepository(abc.ABC):  # noqa: B024
    pass


class BaseS3Repository(BaseRepository, abc.ABC):
    def __init__(self, session: S3Client) -> None:
        self._session = session


class BaseRedisRepository(BaseRepository, abc.ABC):
    def __init__(self, connection_pool: aioredis.ConnectionPool) -> None:
        self._connection_pool = connection_pool

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator["aioredis.Redis[Any]", Any]:
        session: "aioredis.Redis[Any]" = aioredis.Redis(connection_pool=self._connection_pool)
        try:
            async with session.client() as conn:
                yield conn
        finally:
            await session.close()
            await session.connection_pool.disconnect()

    @asynccontextmanager
    async def create_transaction_pipe(
        self, session: "aioredis.Redis[Any]"
    ) -> AsyncGenerator["RedisPipeline[Any]", Any]:
        async with session.pipeline() as pipe:
            yield pipe


class BaseGraphRepository(BaseRedisRepository, abc.ABC):
    def __init__(self, graph_name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.graph_name = graph_name

    def get_graph(self, session: "aioredis.Redis[Any]") -> Graph:
        graph: Graph = session.graph(self.graph_name)
        return graph

    @classmethod
    def create_instance(cls, connection_pool: aioredis.ConnectionPool, graph_name: str) -> Self:
        return cls(
            connection_pool=connection_pool,
            graph_name=graph_name,
        )


class BaseAsyncDBRepository(BaseRepository, abc.ABC):
    def __init__(self, session_manager: async_sessionmaker[AsyncSession]) -> None:
        self._session_manager = session_manager

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        async with self._session_manager() as session:
            yield session
