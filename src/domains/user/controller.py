from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.base.controller import BaseAsyncDBCrudController
from src.domains.oauth.service import JWTService
from src.lib import enums, models, providers, schemas

from .graph_repository import UserGraphRepository
from .repository import UserDBRepository


class UserController(
    BaseAsyncDBCrudController[
        UserDBRepository, models.User, schemas.User, schemas.UsersPaginated, schemas.UserCreate, schemas.UserUpdate
    ]
):
    def __init__(self, db_repo: UserDBRepository, graph_repo: UserGraphRepository, oauth_service: JWTService) -> None:
        self._db_repo = db_repo
        self._graph_repo = graph_repo
        self._oauth_service = oauth_service

    async def me(self, user_id: providers.AuthUserId) -> schemas.User:
        return await super().retrieve(item_id=user_id)

    async def create(self, item: schemas.UserCreate) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            body: dict[str, Any] = item.model_dump()
            password = body.pop("password")
            instance: schemas.User = await self._db_repo.create(
                session=session,
                item=schemas.InnerUserCreate(
                    **body, hashed_password=self._oauth_service.get_password_hash(password=password)
                ),
            )
        return instance

    async def me_update(self, item: schemas.UserUpdate, user_id: providers.AuthUserId) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: schemas.User = await self._db_repo.update(session=session, item=item, item_id=user_id)
            return result

    @staticmethod
    async def get_groups() -> schemas.UserGroupsResponse:
        return schemas.UserGroupsResponse(data=enums.IAMUserGroup.choices())

    async def get_user_groups(self, item_id: int) -> schemas.UserGroupsResponse:
        async with self._graph_repo.create_session() as session:
            data = await self._graph_repo.get_user_groups(session=session, user_id=item_id)
            return schemas.UserGroupsResponse(data=data)

    async def assign_group(
        self, item_id: int, item: schemas.IAMGroupToUserAssign
    ) -> schemas.UserIsGrantedPermissionResponse:
        async with self._graph_repo.create_session() as session:
            valid = await self._graph_repo.assign_group_to_user(
                session=session, user_id=item_id, user_group=item.user_group
            )
            return schemas.UserIsGrantedPermissionResponse(ok=valid)

    async def unassign_group(
        self, item_id: int, item: schemas.IAMGroupToUserAssign
    ) -> schemas.UserIsGrantedPermissionResponse:
        async with self._graph_repo.create_session() as session:
            await self._graph_repo.unassign_group_from_user(
                session=session, user_id=item_id, user_group=item.user_group
            )
            return schemas.UserIsGrantedPermissionResponse()
