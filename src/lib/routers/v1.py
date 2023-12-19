from fastapi import APIRouter

from src.injected import DomainHolder
from src.lib.routers.article import create_article_router
from src.lib.routers.image import create_image_router
from src.lib.routers.oauth import create_oauth_router
from src.lib.routers.user import create_user_router


def create_v1_router(*, domain_holder: DomainHolder) -> APIRouter:
    api_router: APIRouter = APIRouter(prefix="/v1")

    oauth_router: APIRouter = create_oauth_router(domain=domain_holder.oauth)
    user_router: APIRouter = create_user_router(
        domain=domain_holder.user,
        get_authorized=domain_holder.oauth.controller.get_authorized,
        get_access_provided=domain_holder.oauth.controller.get_access_provided,
    )
    article_router: APIRouter = create_article_router(
        domain=domain_holder.article,
        get_authorized=domain_holder.oauth.controller.get_authorized,
        get_access_provided=domain_holder.oauth.controller.get_access_provided,
    )
    image_router: APIRouter = create_image_router(
        domain=domain_holder.image,
        get_access_provided=domain_holder.oauth.controller.get_access_provided,
    )
    api_router.include_router(router=oauth_router)
    api_router.include_router(router=user_router)
    api_router.include_router(router=article_router)
    api_router.include_router(router=image_router)
    return api_router
