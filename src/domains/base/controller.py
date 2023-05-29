import abc
from typing import Any, Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pyfa_converter import QueryDepends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import schemas
from src.lib.models import PgBaseModel
from src.lib.pagination import create_pagination_url_params
from src.lib.schemas import BaseModelWithId, PaginationResponse

DBModelType = TypeVar("DBModelType", bound=PgBaseModel)
DBRepositoryType = TypeVar("DBRepositoryType", bound=BaseAsyncCrudRepository[Any, Any, Any, Any, Any])
PydanticModelType = TypeVar("PydanticModelType", bound=BaseModelWithId)
PydanticModelPaginatedType = TypeVar("PydanticModelPaginatedType", bound=PaginationResponse[Any])
PydanticModelCreateType = TypeVar("PydanticModelCreateType", bound=PydanticBaseModel)
PydanticModelUpdateType = TypeVar("PydanticModelUpdateType", bound=PydanticBaseModel)


# ArticleDBRepository
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

    async def list(
        self,
        pagination_body: schemas.PaginationBody = QueryDepends(schemas.PaginationBody),
    ) -> PaginationResponse[PydanticModelType]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result = await self._db_repo.get_all(
                session=session,
                pagination_body=pagination_body,
            )
        total_pages: int = int(result.count / pagination_body.limit)

        pagination_url_params = create_pagination_url_params(
            request_body=pagination_body,
            items_first_id=result.items[0].id if len(result.items) > 0 else None,
            items_last_id=result.items[-1].id if len(result.items) > 0 else None,
            total_pages=total_pages,
        )
        return schemas.PaginationResponse(
            items=result.items,
            total_items=result.count,
            total_pages=total_pages,
            **pagination_url_params.dict(),
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

    async def delete(self, item_id: int) -> bool:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            return await self._db_repo.delete(session=session, item_id=item_id)
