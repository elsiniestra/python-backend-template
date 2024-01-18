from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.oauth.service import JWTService
from src.lib import enums, pagination, providers, schemas

from .graph_repository import UserGraphRepository
from .repository import UserDBRepository


class UserController:
    def __init__(self, db_repo: UserDBRepository, graph_repo: UserGraphRepository, oauth_service: JWTService) -> None:
        self._db_repo = db_repo
        self._graph_repo = graph_repo
        self._oauth_service = oauth_service

    @pagination.paginated
    async def list(
        self,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.PaginationResponse[schemas.User]:
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
    
    async def retrieve(self, item_id: int) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            return await self._db_repo.get(session=session, item_id=item_id)

    async def create(self, item: schemas.UserCreate) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            return await self._db_repo.create(session=session, item=item)

    async def me(self, user_id: providers.AuthUserId) -> schemas.User:
        return await self.retrieve(item_id=user_id)

    async def create(self, item: schemas.UserCreate) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            body: dict[str, Any] = item.model_dump()
            password = body.pop("password")
            return await self._db_repo.create(
                session=session,
                item=schemas.InnerUserCreate(
                    **body, hashed_password=self._oauth_service.get_password_hash(password=password)
                ),
            )

    async def update(self, item_id: int, item: schemas.UserUpdate) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            return await self._db_repo.update(session=session, item=item, item_id=item_id)

    async def me_update(self, item: schemas.UserUpdate, user_id: providers.AuthUserId) -> schemas.User:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: schemas.User = await self._db_repo.update(session=session, item=item, item_id=user_id)
            return result
        
    async def delete(self, item_id: int) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            await self._db_repo.delete(session=session, item_id=item_id)

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
