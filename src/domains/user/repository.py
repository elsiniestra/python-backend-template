from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import models, schemas


class UserDBRepository(
    BaseAsyncCrudRepository[
        models.User,
        schemas.User,
        schemas.UsersWithCount,
        schemas.InnerUserCreate,
        schemas.UserUpdate,
    ]
):
    @classmethod
    def create_instance(cls, session_manager: "sessionmaker[AsyncSession]") -> "UserDBRepository":
        return cls(
            session_manager=session_manager,
            db_model=models.User,
            pydantic_model=schemas.User,
            pydantic_model_with_count=schemas.UsersWithCount,
            pydantic_create_model=schemas.InnerUserCreate,
            pydantic_update_model=schemas.UserUpdate,
        )

    async def create(self, *, session: AsyncSession, item: schemas.InnerUserCreate) -> schemas.User:
        result = self.db_model(**item.dict())
        session.add(result)
        await session.flush()
        return self.pydantic_model.from_orm(result)
