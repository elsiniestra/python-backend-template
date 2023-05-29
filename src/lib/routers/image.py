from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends

from src.domains import ImageDomain
from src.lib import schemas


def create_image_router(
    *,
    domain: ImageDomain,
    get_authorized: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
    get_access_provided: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/images", tags=["images"], dependencies=[Depends(get_authorized)])
    router.get(path="/{tag}/", response_description="Image file")(domain.controller.get_file)
    router.post(path="/upload/", response_model=schemas.ImageResponse, dependencies=[Depends(get_access_provided)])(
        domain.controller.upload_file_endpoint
    )
    return router
