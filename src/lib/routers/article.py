from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends

from src.domains import ArticleDomain
from src.lib import schemas


def create_article_router(
    *,
    domain: ArticleDomain,
    get_authorized: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
    get_access_provided: Callable[[str, schemas.JwtTokenGenerationInfo], Coroutine[Any, Any, bool]],
) -> APIRouter:
    router: APIRouter = APIRouter(prefix="/articles", tags=["articles"], dependencies=[Depends(get_authorized)])
    router.get(path="/", response_model=schemas.ArticlesPaginated)(domain.controller.list)
    router.post(path="/", response_model=schemas.Article, dependencies=[Depends(get_access_provided)])(
        domain.controller.create
    )
    router.get(path="/{id}/", response_model=schemas.Article)(domain.controller.retrieve)
    router.patch(path="/{id}/", response_model=schemas.Article, dependencies=[Depends(get_access_provided)])(
        domain.controller.update
    )
    router.delete(path="/{id}/", response_model=bool, dependencies=[Depends(get_access_provided)])(
        domain.controller.delete
    )
    router.get(path="/{article_id}/comments/")(domain.controller.get_root_comments)
    router.get(path="/{article_id}/comments/{comment_id}/answers/")(domain.controller.get_comment_answers)
    router.post(path="/{article_id}/comments/")(domain.controller.create_comment)
    router.put(path="/{article_id}/comments/{comment_id}/")(domain.controller.update_comment)
    router.delete(path="/{article_id}/comments/{comment_id}/")(domain.controller.delete_comment)
    return router
