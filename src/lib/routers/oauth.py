from fastapi import APIRouter
from starlette import status

from src.domains import OauthDomain
from src.lib import schemas


def create_oauth_router(*, domain: OauthDomain) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/oauth", tags=["oauth"])
    router.post(path="/rotate-token/", response_model=schemas.RotateTokenResponse, status_code=status.HTTP_201_CREATED)(
        domain.controller.rotate_access_and_refresh_token
    )
    router.post(
        path="/refresh-token/", response_model=schemas.RotateTokenResponse, status_code=status.HTTP_201_CREATED
    )(domain.controller.refresh_access_token)
    router.get(path="/sso/google/init", status_code=status.HTTP_200_OK)(domain.controller.google_sso_init)
    router.get(path="/sso/google/callback", status_code=status.HTTP_200_OK)(domain.controller.google_sso_callback)
    router.get(path="/sso/github/init", status_code=status.HTTP_200_OK)(domain.controller.github_sso_init)
    router.get(path="/sso/github/callback", status_code=status.HTTP_200_OK)(domain.controller.github_sso_callback)
    router.get(path="/sso/microsoft/init", status_code=status.HTTP_200_OK)(domain.controller.microsoft_sso_init)
    router.get(path="/sso/microsoft/callback", status_code=status.HTTP_200_OK)(domain.controller.microsoft_sso_callback)
    return router
