from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import errors, models, pagination, schemas


class UserDBRepository(
    BaseAsyncCrudRepository[
        models.User,
        schemas.User,
        schemas.UsersWithCount,
        schemas.InnerUserCreate,
        schemas.UserUpdate,
    ]
):
    async def get(self, *, session: AsyncSession, item_id: int) -> schemas.User:
        query = select(
            self.db_model.id,
            self.db_model.email,
            self.db_model.username,
            self.db_model.first_name,
            self.db_model.last_name,
        ).where(self.db_model.id == item_id)
        result = (await session.execute(query)).mappings().first()
        if result is None:
            raise errors.UserNotFoundError()
        return self.pydantic_model(**result)

    async def get_all(
        self,
        *,
        session: AsyncSession,
        pagination_body: schemas.PaginationBody,
    ) -> schemas.UsersWithCount:
        paginated_query = pagination.add_pagination_to_query(
            query=select(self.db_model.__table__), id_column=self.db_model.id, body=pagination_body
        )
        result = await session.execute(paginated_query)
        items = result.mappings().all()
        total_count = await self._get_rows_count_in(session=session, table=self.db_model)

        return self.pydantic_model_with_count(items=items, count=total_count)

    @classmethod
    def create_instance(cls, session_manager: async_sessionmaker[AsyncSession]) -> "UserDBRepository":
        return cls(
            session_manager=session_manager,
            db_model=models.User,
            pydantic_model=schemas.User,
            pydantic_model_with_count=schemas.UsersWithCount,
            pydantic_create_model=schemas.InnerUserCreate,
            pydantic_update_model=schemas.UserUpdate,
        )
