from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends
from starlette import status

from src.domains import UserDomain
from src.lib import enums, schemas


def _create_no_auth_router(domain: UserDomain) -> APIRouter:
    no_auth_router: APIRouter = APIRouter(prefix="/users", tags=["users"])
    no_auth_router.get(path="/{item_id}/", response_model=schemas.User, status_code=status.HTTP_200_OK)(
        domain.controller.retrieve
    )
    no_auth_router.post(path="/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)(
        domain.controller.create
    )
    return no_auth_router


def _create_auth_router(
    domain: UserDomain,
    get_authorized: Callable[[int], Coroutine[Any, Any, bool]],
) -> APIRouter:
    auth_router: APIRouter = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_authorized)])
    auth_router.get(path="/me/", response_model=schemas.User, status_code=status.HTTP_200_OK)(domain.controller.me)
    auth_router.patch(path="/me/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)(
        domain.controller.me_update
    )
    # TODO: DELETE /me/
    return auth_router


def _create_admin_read_router(
    domain: UserDomain,
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    admin_read_router: APIRouter = APIRouter(
        prefix="/admin/users",
        tags=["users", "admin"],
        dependencies=[
            Depends(get_access_provided(enums.IAMScope.ADMIN_USERS, enums.IAMAccess.READ)),
        ],
    )
    admin_read_router.get(path="/", response_model=schemas.UsersPaginated, status_code=status.HTTP_200_OK)(
        domain.controller.list
    )

    admin_read_router.get(path="/groups/", response_model=schemas.UserGroupsResponse, status_code=status.HTTP_200_OK)(
        domain.controller.get_groups
    )
    admin_read_router.get(
        path="/{item_id}/groups/", response_model=schemas.UserGroupsResponse, status_code=status.HTTP_200_OK
    )(domain.controller.get_user_groups)
    return admin_read_router


def _create_admin_write_router(
    domain: UserDomain,
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    admin_write_router: APIRouter = APIRouter(
        prefix="/admin/users",
        tags=["users", "admin"],
        dependencies=[
            Depends(get_access_provided(enums.IAMScope.ADMIN_USERS, enums.IAMAccess.WRITE)),
        ],
    )
    admin_write_router.patch(
        path="/{item_id}/add-group/",
        response_model=schemas.UserIsGrantedPermissionResponse,
        status_code=status.HTTP_201_CREATED,
    )(domain.controller.assign_group)
    admin_write_router.patch(
        path="/{item_id}/remove-group/",
        response_model=schemas.UserIsGrantedPermissionResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(get_access_provided(enums.IAMScope.ADMIN_USERS, enums.IAMAccess.WRITE))],
    )(domain.controller.unassign_group)

    admin_write_router.delete(
        path="/{item_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
    )(domain.controller.delete)
    return admin_write_router


def create_user_router(
    *,
    domain: UserDomain,
    get_authorized: Callable[[int], Coroutine[Any, Any, bool]],
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    router: APIRouter = APIRouter()
    router.include_router(router=_create_auth_router(domain, get_authorized))
    router.include_router(router=_create_no_auth_router(domain))
    router.include_router(router=_create_admin_read_router(domain, get_access_provided))
    router.include_router(router=_create_admin_write_router(domain, get_access_provided))
    return router
