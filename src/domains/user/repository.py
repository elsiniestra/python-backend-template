from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base.repository import BaseAsyncDBRepository
from src.lib import errors, models, pagination, schemas


class UserDBRepository(BaseAsyncDBRepository):
    async def get(self, *, session: AsyncSession, item_id: int) -> schemas.User:
        query = select(
            models.User.id,
            models.User.email,
            models.User.username,
            models.User.first_name,
            models.User.last_name,
        ).where(models.User.id == item_id)
        result = (await session.execute(query)).mappings().first()
        if result is None:
            raise errors.UserNotFoundError()
        return schemas.User(**result)

    async def get_all(
        self,
        *,
        session: AsyncSession,
        pagination_body: schemas.PaginationBody,
    ) -> schemas.UsersWithCount:
        paginated_query = pagination.add_pagination_to_query(
            query=select(models.User.__table__), id_column=models.User.id, body=pagination_body
        )
        result = await session.execute(paginated_query)
        items = result.mappings().all()
        total_count = await self._get_rows_count_in(session=session, table=models.User)

        return schemas.UsersWithCount(items=items, count=total_count)

    async def create(self, *, session: AsyncSession, item: schemas.UserCreate) -> schemas.User:
        result = models.User(**item.model_dump())
        session.add(result)
        await session.flush()
        return await self.get(session=session, item_id=result.id)

    async def update(
        self, *, session: AsyncSession, item: schemas.UserUpdate, item_id: int
) -> schemas.UserUpdate:
        body = item.model_dump(exclude_unset=True)
        if body == {}:
            raise errors.UnprocessableEntityError()
        result = await self.get(session=session, item_id=item_id)
        if result is None:
            raise errors.NotFoundError()
        await session.execute(update(models.User).where(models.User.id == item_id).values(**body))
        return await self.get(session=session, item_id=item_id)

    @staticmethod
    async def delete(*, session: AsyncSession, item_id: int) -> bool:
        result = await session.get(models.User, item_id)
        if result is None:
            raise errors.NotFoundError()
        await session.delete(result)
        return True

    @staticmethod
    async def _get_rows_count_in(*, session: AsyncSession) -> int:
        res = (await session.execute(func.count(models.User.id))).scalar()
        if not isinstance(res, int):
            raise errors.UnprocessableEntityError(detail="Count query returned non-int value")
        return res
