import abc

from fastapi import Depends
from pyfa_converter import QueryDepends
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.article.repository import ArticleDBRepository
from src.domains.base.controller import BaseAsyncDBCrudController
from src.lib import models, providers, schemas, utils
from src.lib.errors import OperationWithNonUserCommentError
from src.lib.pagination import create_pagination_url_params


class ArticleController(
    BaseAsyncDBCrudController[
        ArticleDBRepository,
        models.Article,
        schemas.Article,
        schemas.ArticlesPaginated,
        schemas.ArticleCreate,
        schemas.ArticleCreate,
    ],
    abc.ABC,
):
    def __init__(self, db_repo: ArticleDBRepository) -> None:
        self._db_repo = db_repo

    async def create(self, item: schemas.ArticleCreate) -> schemas.Article:
        slug: str = slugify(f"{item.title}-{utils.get_current_timestamp()}")
        return await self.create(item=schemas.InnerArticleCreate(**item.dict(), slug=slug))

    async def update(self, item_id: int, item: schemas.ArticleCreate) -> schemas.Article:
        slug: str = slugify(f"{item.title}-{utils.get_current_timestamp()}")
        return await self.update(item_id=item_id, item=schemas.InnerArticleCreate(**item.dict(), slug=slug))

    async def get_root_comments(
        self, item_id: int, pagination_body: schemas.PaginationBody = QueryDepends(schemas.PaginationBody)
    ) -> schemas.CommentsPaginated:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: schemas.CommentsWithCount = await self._db_repo.get_root_comments(
                session=session, article_id=item_id, pagination_body=pagination_body
            )
        total_pages: int = int(result.count / pagination_body.limit)

        pagination_url_params = create_pagination_url_params(
            request_body=pagination_body,
            items_first_id=result.items[0].id if len(result.items) > 0 else None,
            items_last_id=result.items[-1].id if len(result.items) > 0 else None,
            total_pages=total_pages,
        )
        return schemas.CommentsPaginated(
            items=result.items,
            total_items=result.count,
            total_pages=total_pages,
            **pagination_url_params.dict(),
        )

    async def get_comment_answers(
        self, comment_id: int, pagination_body: schemas.PaginationBody = QueryDepends(schemas.PaginationBody)
    ) -> schemas.CommentsPaginated:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: schemas.CommentsWithCount = await self._db_repo.get_comment_answers(
                session=session, comment_id=comment_id, pagination_body=pagination_body
            )
        total_pages: int = int(result.count / pagination_body.limit)

        pagination_url_params = create_pagination_url_params(
            request_body=pagination_body,
            items_first_id=result.items[0].id if len(result.items) > 0 else None,
            items_last_id=result.items[-1].id if len(result.items) > 0 else None,
            total_pages=total_pages,
        )
        return schemas.CommentsPaginated(
            items=result.items,
            total_items=result.count,
            total_pages=total_pages,
            **pagination_url_params.dict(),
        )

    async def create_comment(
        self, item_id: int, item: schemas.CommentCreate, requester_id: int = Depends(providers.get_auth_user_id)
    ) -> schemas.Comment:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: schemas.Comment = await self._db_repo.create_comment(
                session=session, article_id=item_id, author_id=requester_id, item=item
            )
            return result

    async def update_comment(
        self, comment_id: int, item: schemas.CommentUpdate, requester_id: int = Depends(providers.get_auth_user_id)
    ) -> schemas.Comment:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            author_id: int = await self._db_repo.get_comment_author_id(session=session, comment_id=comment_id)
            if author_id != requester_id:
                raise OperationWithNonUserCommentError
            result: schemas.Comment = await self._db_repo.update_comment(
                session=session, comment_id=comment_id, item=item
            )
            return result

    async def delete_comment(self, comment_id: int, requester_id: int = Depends(providers.get_auth_user_id)) -> bool:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            author_id: int = await self._db_repo.get_comment_author_id(session=session, comment_id=comment_id)
            if author_id != requester_id:
                raise OperationWithNonUserCommentError
            result: bool = await self._db_repo.delete_comment(session=session, comment_id=comment_id)
            return result
