import abc
from typing import Any, Generic, TypeVar

from fastapi import Depends
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import models, pagination, schemas

DBModelType = TypeVar("DBModelType", bound=models.PgBaseModel)
DBRepositoryType = TypeVar("DBRepositoryType", bound=BaseAsyncCrudRepository[Any, Any, Any, Any, Any])
PydanticModelType = TypeVar("PydanticModelType", bound=schemas.BaseModelWithId)
PydanticModelPaginatedType = TypeVar("PydanticModelPaginatedType", bound=schemas.PaginationResponse[Any])
PydanticModelCreateType = TypeVar("PydanticModelCreateType", bound=PydanticBaseModel)
PydanticModelUpdateType = TypeVar("PydanticModelUpdateType", bound=PydanticBaseModel)


class BaseAsyncDBCrudController(
    abc.ABC,
    Generic[
        DBRepositoryType,
        DBModelType,
        PydanticModelType,
        PydanticModelPaginatedType,
        PydanticModelCreateType,
        PydanticModelUpdateType,
    ],
):
    @abc.abstractmethod
    def __init__(self, db_repo: DBRepositoryType) -> None:
        self._db_repo = db_repo

    @pagination.paginated
    async def list(
        self,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.PaginationResponse[PydanticModelType]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result = await self._db_repo.get_all(
                session=session,
                pagination_body=pagination_body,
            )
        return schemas.PaginationResponse(
            items=result.items,
            total_items=result.count,
        )

    async def create(self, item: PydanticModelCreateType) -> PydanticModelType:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: PydanticModelType = await self._db_repo.create(session=session, item=item)
            return result

    async def retrieve(self, item_id: int) -> PydanticModelType:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: PydanticModelType = await self._db_repo.get(session=session, item_id=item_id)
            return result

    async def update(self, item_id: int, item: PydanticModelUpdateType) -> PydanticModelType:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: PydanticModelType = await self._db_repo.update(session=session, item=item, item_id=item_id)
            return result

    async def delete(self, item_id: int) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            await self._db_repo.delete(session=session, item_id=item_id)
