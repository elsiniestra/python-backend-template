from typing import Any, Callable, Coroutine

from fastapi import APIRouter, Depends
from starlette import status

from src.domains import ArticleDomain
from src.lib import enums, schemas


def _create_no_auth_router(domain: ArticleDomain) -> APIRouter:
    no_auth_router: APIRouter = APIRouter(prefix="/articles", tags=["articles"])
    no_auth_router.get(path="/", response_model=schemas.ArticlesPaginated, status_code=status.HTTP_200_OK)(
        domain.controller.list
    )
    no_auth_router.get(path="/main/", response_model=schemas.ArticlesResponse, status_code=status.HTTP_200_OK)(
        domain.controller.list_main_only
    )
    no_auth_router.get(path="/{slug}/", response_model=schemas.Article, status_code=status.HTTP_200_OK)(
        domain.controller.retrieve
    )
    no_auth_router.get(
        path="/{item_id}/comments/", response_model=schemas.CommentsPaginated, status_code=status.HTTP_200_OK
    )(domain.controller.get_root_comments)
    no_auth_router.get(
        path="/{item_id}/comments/{comment_id}/answers/",
        response_model=schemas.CommentsPaginated,
        status_code=status.HTTP_200_OK,
    )(domain.controller.get_comment_answers)
    return no_auth_router


def _create_auth_router(domain: ArticleDomain, get_authorized: Callable[[int], Coroutine[Any, Any, bool]]) -> APIRouter:
    auth_router: APIRouter = APIRouter(prefix="/articles", tags=["articles"], dependencies=[Depends(get_authorized)])
    auth_router.post(path="/{slug}/like/", status_code=status.HTTP_201_CREATED)(domain.controller.like)
    auth_router.delete(path="/{slug}/like/", status_code=status.HTTP_204_NO_CONTENT)(domain.controller.delete_like)
    auth_router.post(path="/{item_id}/comments/", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)(
        domain.controller.create_comment
    )
    auth_router.patch(
        path="/{item_id}/comments/{comment_id}/", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED
    )(domain.controller.update_comment)
    auth_router.delete(path="/{item_id}/comments/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT)(
        domain.controller.delete_comment
    )
    auth_router.post(path="/{item_id}/comments/{comment_id}/like/", status_code=status.HTTP_201_CREATED)(
        domain.controller.like_comment
    )
    auth_router.delete(path="/{item_id}/comments/{comment_id}/like/", status_code=status.HTTP_204_NO_CONTENT)(
        domain.controller.delete_comment_like
    )
    return auth_router


def _create_admin_router(
    domain: ArticleDomain,
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    admin_router: APIRouter = APIRouter(
        prefix="/admin/articles",
        tags=["articles", "admin"],
        dependencies=[Depends(get_access_provided(enums.IAMScope.ADMIN_POSTS, enums.IAMAccess.WRITE))],
    )
    admin_router.get(path="/", status_code=status.HTTP_200_OK, response_model=schemas.ArticlesEditorResponse)(
        domain.controller.list_editor
    )
    admin_router.post(path="/", status_code=status.HTTP_201_CREATED, response_model=schemas.ArticleCreateResponse)(
        domain.controller.create
    )
    admin_router.patch(path="/{slug}/", status_code=status.HTTP_201_CREATED, response_model=schemas.Article)(
        domain.controller.update
    )
    admin_router.delete(path="/{slug}/", status_code=status.HTTP_204_NO_CONTENT)(domain.controller.delete)
    return admin_router


def create_article_router(
    *,
    domain: ArticleDomain,
    get_authorized: Callable[[int], Coroutine[Any, Any, bool]],
    get_access_provided: Callable[[enums.IAMScope, enums.IAMAccess], Callable[[int], Coroutine[Any, Any, bool]]],
) -> APIRouter:
    router: APIRouter = APIRouter()
    router.include_router(router=_create_no_auth_router(domain))
    router.include_router(router=_create_auth_router(domain, get_authorized))
    router.include_router(router=_create_admin_router(domain, get_access_provided))
    return router
