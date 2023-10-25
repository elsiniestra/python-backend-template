from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends
from starlette import status

from src.domains import ImageDomain
from src.lib import enums, schemas


def create_image_router(
    *,
    domain: ImageDomain,
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/admin/images",
        tags=["images", "admin"],
        dependencies=[Depends(get_access_provided(enums.IAMScope.ADMIN_POSTS, enums.IAMAccess.WRITE))],
    )
    router.get(path="/", status_code=status.HTTP_200_OK, response_description="Image file")(domain.controller.get_file)
    router.post(path="/upload/", status_code=status.HTTP_201_CREATED, response_model=schemas.ImageResponse)(
        domain.controller.upload_file_endpoint
    )
    return router
