from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.base.controller import BaseAsyncDBCrudController
from src.domains.oauth.service import JWTService
from src.lib import models, schemas

from .graph_repository import BaseUserGraphRepository
from .repository import UserDBRepository


class UserController(
    BaseAsyncDBCrudController[
        UserDBRepository, models.User, schemas.User, schemas.UsersPaginated, schemas.UserCreate, schemas.UserUpdate
    ]
):
    def __init__(
        self, db_repo: UserDBRepository, graph_repo: BaseUserGraphRepository, oauth_service: JWTService
    ) -> None:
        self._db_repo = db_repo
        self._graph_repo = graph_repo
        self._oauth_service = oauth_service

    async def create(self, item: schemas.UserCreate) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            body: dict[str, Any] = item.dict()
            password = body.pop("password")
            instance: schemas.User = await self._db_repo.create(
                session=session,
                item=schemas.InnerUserCreate(
                    **body, hashed_password=self._oauth_service.get_password_hash(password=password)
                ),
            )
        return instance

    async def assign_group(self, item: schemas.IAMGroupToUserAssign) -> Literal[True]:
        async with self._graph_repo.create_session() as session:
            return await self._graph_repo.assign_group_to_user(
                session=session, user_id=item.user_id, user_group=item.user_group
            )
