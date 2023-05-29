from fastapi import APIRouter

from src.domains import OauthDomain
from src.lib import schemas


def create_oauth_router(*, domain: OauthDomain) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/oauth", tags=["oauth"])
    router.post(path="/rotate-token/", response_model=schemas.RotateTokenResponse)(
        domain.controller.rotate_access_and_refresh_token
    )
    router.post(path="/refresh-token/", response_model=schemas.RotateTokenResponse)(
        domain.controller.refresh_access_token
    )
    return router
