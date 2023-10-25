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


class BaseAsyncCrudRepository(
    BaseAsyncDBRepository,
    Generic[
        DBModelType,
        PydanticModelType,
        PydanticModelWithCountType,
        PydanticModelCreateType,
        PydanticModelUpdateType,
    ],
):
    def __init__(
        self,
        session_manager: async_sessionmaker[AsyncSession],
        db_model: type[DBModelType],
        pydantic_model: type[PydanticModelType],
        pydantic_model_with_count: type[PydanticModelWithCountType],
        pydantic_create_model: type[PydanticModelCreateType],
        pydantic_update_model: type[PydanticModelUpdateType],
    ) -> None:
        super().__init__(session_manager=session_manager)
        self.db_model = db_model
        self.pydantic_model = pydantic_model
        self.pydantic_model_with_count = pydantic_model_with_count
        self.pydantic_create_model = pydantic_create_model
        self.pydantic_update_model = pydantic_update_model

    async def get(self, *, session: AsyncSession, item_id: int) -> PydanticModelType:  # noqa: A002
        query = select(self.db_model.__table__).where(self.db_model.id == item_id)
        result = (await session.execute(query)).mappings().first()
        if result is None:
            raise errors.NotFoundError()
        return self.pydantic_model(**result)

    async def create(self, *, session: AsyncSession, item: PydanticModelCreateType) -> PydanticModelType:
        result = self.db_model(**item.model_dump())
        session.add(result)
        await session.flush()
        return await self.get(session=session, item_id=result.id)

    async def update(
        self, *, session: AsyncSession, item: PydanticModelUpdateType, item_id: int
    ) -> PydanticModelType:  # noqa: A002
        body = item.model_dump(exclude_unset=True)
        if body == {}:
            raise errors.UnprocessableEntityError()
        result = await self.get(session=session, item_id=item_id)
        if result is None:
            raise errors.NotFoundError()
        await session.execute(update(self.db_model).where(self.db_model.id == item_id).values(**body))
        return await self.get(session=session, item_id=item_id)

    async def delete(self, *, session: AsyncSession, item_id: int) -> bool:  # noqa: A002
        result = await session.get(self.db_model, item_id)
        if result is None:
            raise errors.NotFoundError()
        await session.delete(result)
        return True

    @staticmethod
    async def _get_rows_count_in(*, session: AsyncSession, table: type[DBModelType]) -> int:
        res = (await session.execute(func.count(table.id))).scalar()
        if not isinstance(res, int):
            raise errors.UnprocessableEntityError(detail="Count query returned non-int value")
        return res

    async def get_all(
        self,
        *,
        session: AsyncSession,
        pagination_body: schemas.PaginationBody,
    ) -> PydanticModelWithCountType:
        paginated_query = pagination.add_pagination_to_query(
            query=select(self.db_model.__table__), id_column=self.db_model.id, body=pagination_body
        )
        result = await session.execute(paginated_query)
        items = result.mappings().all()
        total_count = await self._get_rows_count_in(session=session, table=self.db_model)

        return self.pydantic_model_with_count(items=items, count=total_count)
