from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends

from src.domains import UserDomain
from src.lib import schemas


def create_user_router(
    *,
    domain: UserDomain,
    get_authorized: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
    get_access_provided: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_authorized)])
    router.get(path="/", response_model=schemas.UsersPaginated)(domain.controller.list)
    router.post(path="/", response_model=schemas.User)(domain.controller.create)
    router.get(path="/{id}/", response_model=schemas.User)(domain.controller.retrieve)
    router.patch(path="/{id}/", response_model=schemas.User)(domain.controller.update)
    router.patch(
        path="/{id}/add-group/",
        response_model=schemas.UserIsGrantedPermissionResponse,
        dependencies=[Depends(get_access_provided)],
    )(domain.controller.assign_group)
    router.delete(path="/{id}/", response_model=bool)(domain.controller.delete)
    return router
