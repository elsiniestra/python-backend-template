import abc
import io
import uuid
from typing import Literal
from urllib.parse import urljoin, urlparse

import aiofiles
import imgkit
from fastapi import BackgroundTasks, Depends, Request, UploadFile
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import Headers

from src.domains.base.controller import BaseAsyncDBCrudController
from src.lib import errors, models, pagination, providers, schemas, utils

from .repository import ArticleDBRepository


# TODO: split into smaller parts
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

    async def retrieve(self, request: Request, slug: str) -> schemas.Article:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: schemas.Article = await self._db_repo.get(
                session=session,
                slug=slug,
                language=utils.i18n.get_accept_language_best_match(request.headers.get("accept-language")),
            )
            return result

    async def list_main_only(self, request: Request) -> schemas.ArticlesResponse:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result = await self._db_repo.get_all(
                session=session,
                language=utils.i18n.get_accept_language_best_match(request.headers.get("accept-language")),
                is_main=True,
            )

        return schemas.ArticlesResponse(items=result.items)

    @pagination.paginated
    async def list(
        self,
        request: Request,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.PaginationResponse[schemas.ArticleShort]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result = await self._db_repo.get_all(
                session=session,
                pagination_body=pagination_body,
                language=utils.i18n.get_accept_language_best_match(request.headers.get("accept-language")),
            )

        return schemas.PaginationResponse(
            items=result.items,
            total_items=result.count,
        )

    @pagination.paginated
    async def list_editor(
        self,
        request: Request,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.PaginationResponse[schemas.ArticleShortEditor]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result = await self._db_repo.get_all_admin(
                session=session,
                pagination_body=pagination_body,
                language=utils.i18n.get_accept_language_best_match(request.headers.get("accept-language")),
            )

        return schemas.PaginationResponse(
            items=result.items,
            total_items=result.count,
        )

    async def create(
        self,
        request: Request,
        item: schemas.ArticleCreate,
        background_tasks: BackgroundTasks,
        domain_holder: providers.DomainHolderRequired,
        settings: providers.MainSettingsRequired,
    ) -> schemas.ArticleCreateResponse:
        data = item.model_dump()
        data["slug"] = slugify(f"{item.title}-{utils.get_current_timestamp()}")
        data["generic_id"] = data["generic_id"] or uuid.uuid4()
        async with self._db_repo.get_session() as session, session.begin():
            result = await self._db_repo.create(session=session, item=schemas.InnerArticleCreate(**data))
            if not settings.environment.is_testing:
                background_tasks.add_task(
                    self.generate_preview_article,
                    item=result,
                    domain_holder=domain_holder,
                    settings=settings,
                    request=request,
                )
            return result

    async def update(self, request: Request, slug: str, item: schemas.ArticleUpdate) -> schemas.Article:
        if item.model_dump(exclude_unset=True) == {}:
            raise errors.UnprocessableEntityError()
        async with self._db_repo.get_session() as session, session.begin():
            return await self._db_repo.update(
                session=session,
                slug=slug,
                item=item,
                language=utils.i18n.get_accept_language_best_match(request.headers.get("accept-language")),
            )

    async def delete(self, slug: str) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            await self._db_repo.delete(session=session, slug=slug)

    async def like(self, slug: str, user_id: providers.AuthUserId, is_positive: bool = True) -> Literal[True]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            await self._db_repo.like(
                session=session,
                slug=slug,
                user_id=user_id,
                is_positive=is_positive,
            )
            return True

    async def delete_like(self, slug: str, user_id: providers.AuthUserId) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            await self._db_repo.delete_like(
                session=session,
                slug=slug,
                user_id=user_id,
            )

    @pagination.paginated
    async def get_root_comments(
        self,
        item_id: int,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.CommentsPaginated:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: schemas.CommentsWithCount = await self._db_repo.get_root_comments(
                session=session, article_id=item_id, pagination_body=pagination_body
            )
        return schemas.CommentsPaginated(
            items=result.items,
            total_items=result.count,
        )

    @pagination.paginated
    async def get_comment_answers(
        self,
        comment_id: int,
        pagination_body: schemas.PaginationBody = Depends(),
    ) -> schemas.CommentsPaginated:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            result: schemas.CommentsWithCount = await self._db_repo.get_comment_answers(
                session=session, comment_id=comment_id, pagination_body=pagination_body
            )
        return schemas.CommentsPaginated(
            items=result.items,
            total_items=result.count,
        )

    async def create_comment(
        self, item_id: int, item: schemas.CommentCreate, requester_id: providers.AuthUserId
    ) -> schemas.Comment:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            result: schemas.Comment = await self._db_repo.create_comment(
                session=session, article_id=item_id, author_id=requester_id, item=item
            )
            return result

    async def update_comment(
        self, comment_id: int, item: schemas.CommentUpdate, requester_id: providers.AuthUserId
    ) -> schemas.Comment:
        session: AsyncSession
        async with self._db_repo.get_session() as session, session.begin():
            author_id: int = await self._db_repo.get_comment_author_id(session=session, comment_id=comment_id)
            if author_id != requester_id:  # TODO: move this to DB repo to reduce the amount of SQL queries
                raise errors.OperationWithNonUserCommentError
            result: schemas.Comment = await self._db_repo.update_comment(
                session=session, comment_id=comment_id, item=item
            )
            return result

    async def delete_comment(self, comment_id: int, requester_id: providers.AuthUserId) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            author_id: int = await self._db_repo.get_comment_author_id(session=session, comment_id=comment_id)
            if author_id != requester_id:
                raise errors.OperationWithNonUserCommentError
            await self._db_repo.delete_comment(session=session, comment_id=comment_id)

    async def like_comment(
        self, comment_id: int, requester_id: providers.AuthUserId, is_positive: bool = True
    ) -> Literal[True]:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            await self._db_repo.like_comment(
                session=session, comment_id=comment_id, user_id=requester_id, is_positive=is_positive
            )
            return True

    async def delete_comment_like(self, comment_id: int, requester_id: providers.AuthUserId) -> None:
        session: AsyncSession
        async with self._db_repo.get_session() as session:
            await self._db_repo.delete_comment_like(session=session, comment_id=comment_id, user_id=requester_id)

    async def generate_preview_article(
        self,
        request: Request,
        item: schemas.ArticleCreateResponse,
        domain_holder: providers.DomainHolderRequired,
        settings: providers.MainSettingsRequired,
    ) -> None:
        async with aiofiles.open(file=f"{settings.asset_path.templates}/article-preview-template.html") as file:
            content: str = await file.read()
            image: bytes = imgkit.from_string(
                string=content.format(title=item.title, label=item.label, image=item.cover_image),
                output_path=False,
                options={"format": "png"},
            )
            upload_file = UploadFile(
                file=io.BytesIO(image),
                filename=f"{item.slug}-preview.png",
                headers=Headers({"content-type": "image/png"}),
            )
            preview_url = (
                await domain_holder.image.controller.upload_file_endpoint(
                    file=upload_file, folder="articles/previews", settings=settings
                )
            ).url

            await self.update(
                request=request,
                slug=item.slug,
                item=schemas.ArticleUpdate(preview_image=urljoin(preview_url, urlparse(preview_url).path)),
            )
