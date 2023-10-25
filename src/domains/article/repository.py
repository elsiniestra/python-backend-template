from sqlalchemy import (
    GenerativeSelect,
    and_,
    case,
    delete,
    distinct,
    exists,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import aggregate_order_by, array_agg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.functions import coalesce

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import enums, errors, models, pagination, schemas


class ArticleDBRepository(
    BaseAsyncCrudRepository[
        models.Article,
        schemas.Article,
        schemas.ArticlesWithCount,
        schemas.ArticleCreate,
        schemas.ArticleCreate,
    ]
):
    @classmethod
    def create_instance(cls, session_manager: async_sessionmaker[AsyncSession]) -> "ArticleDBRepository":
        return cls(
            session_manager=session_manager,
            db_model=models.Article,
            pydantic_model=schemas.Article,
            pydantic_model_with_count=schemas.ArticlesWithCount,
            pydantic_create_model=schemas.ArticleCreate,
            pydantic_update_model=schemas.ArticleCreate,
        )

    async def get(self, *, session: AsyncSession, slug: str, language: enums.LanguageType) -> schemas.Article:
        query = (
            self._get_query(language=language)
            .add_columns(
                self.db_model.label,
                self.db_model.preview_image,
                self.db_model.content,
                self.db_model.created_at,
                self.db_model.updated_at,
                self.db_model.language,
            )
            .where(and_(self.db_model.slug == slug, self.db_model.is_draft == False))  # noqa: E712
        )
        result = (await session.execute(query)).mappings().first()
        if result is None:
            raise errors.ArticleNotFoundError()
        return self.pydantic_model(**result)

    async def get_admin(
        self, *, session: AsyncSession, slug: str, language: enums.LanguageType
    ) -> schemas.ArticleEditor:
        query = (
            self._get_query(language=language)
            .add_columns(
                self.db_model.label,
                self.db_model.preview_image,
                self.db_model.content,
                self.db_model.created_at,
                self.db_model.updated_at,
                self.db_model.language,
                self.db_model.generic_id,
                self.db_model.is_main,
                self.db_model.is_draft,
            )
            .where(self.db_model.slug == slug)
        )
        result = (await session.execute(query)).mappings().first()
        if result is None:
            raise errors.ArticleNotFoundError()
        return schemas.ArticleEditor(**result)

    async def create(self, *, session: AsyncSession, item: schemas.ArticleCreate) -> schemas.ArticleCreateResponse:
        params = item.model_dump()
        tags = params.pop("tags")
        result = self.db_model(**params)
        session.add(result)
        await session.flush()
        for tag in tags:
            tag_id = (await session.execute(select(models.Tag.id).where(models.Tag.name == tag))).scalar() or (
                await session.execute(insert(models.Tag).values(name=tag).returning(models.Tag.id))
            ).scalar()
            session.add(models.ArticlesToTags(tag_id=tag_id, article_id=result.id))
        await session.flush()
        result.tags = tags
        return schemas.ArticleCreateResponse.model_validate(result)

    async def get_all(
        self,
        *,
        session: AsyncSession,
        language: enums.LanguageType,
        pagination_body: schemas.PaginationBody = None,
        is_main: bool = False,
    ) -> schemas.ArticlesWithCount:
        if not is_main and not pagination_body:
            raise errors.InvalidArticleListQueryError()

        query = self._get_query(language=language).where(self.db_model.is_draft == False)  # noqa: E712

        if pagination_body:
            query = pagination.add_pagination_to_query(query=query, id_column=self.db_model.id, body=pagination_body)
        if is_main:
            query = query.where(self.db_model.is_main == True).limit(4).order_by(self.db_model.created_at)  # noqa: E712

        result = await session.execute(query)
        items = result.mappings().all()

        query = select(func.count(distinct(self.db_model.generic_id))).where(
            and_(self.db_model.language == language, self.db_model.is_draft == False)  # noqa: E712
        )

        total_count = (await session.execute(query)).scalar()
        return self.pydantic_model_with_count(items=items, count=total_count)

    async def get_all_admin(
        self,
        *,
        session: AsyncSession,
        language: enums.LanguageType,
        pagination_body: schemas.PaginationBody = None,
    ) -> schemas.ArticlesEditorWithCount:
        if not pagination_body:
            raise errors.InvalidArticleListQueryError()

        query = self._get_query(language=language).add_columns(self.db_model.is_draft, self.db_model.is_main)
        if pagination_body:
            query = pagination.add_pagination_to_query(query=query, id_column=self.db_model.id, body=pagination_body)

        result = await session.execute(query)
        items = result.mappings().all()

        query = select(func.count(distinct(self.db_model.generic_id))).where(and_(self.db_model.language == language))

        total_count = (await session.execute(query)).scalar()
        return schemas.ArticlesEditorWithCount(items=items, count=total_count)

    async def update(
        self, *, session: AsyncSession, item: schemas.ArticleUpdate, slug: str, language: enums.LanguageType
    ) -> schemas.Article:
        body = item.model_dump(exclude_unset=True)
        tags = body.pop("tags") if body.get("tags") else None
        article_id = (
            (
                await session.execute(
                    update(self.db_model).where(self.db_model.slug == slug).values(**body).returning(self.db_model.id)
                )
            )
            .scalars()
            .first()
        )
        if tags:
            article_tag_ids = []
            for tag in tags:
                tag_id = (await session.execute(select(models.Tag.id).where(models.Tag.name == tag))).scalar() or (
                    await session.execute(insert(models.Tag).values(name=tag).returning(models.Tag.id))
                ).scalar()

                if not (
                    await session.execute(
                        select(exists(models.ArticlesToTags)).where(
                            and_(models.ArticlesToTags.article_id == article_id, models.ArticlesToTags.tag_id == tag_id)
                        )
                    )
                ).scalar():
                    session.add(models.ArticlesToTags(tag_id=tag_id, article_id=article_id))
                article_tag_ids.append(tag_id)
            await session.execute(
                delete(models.ArticlesToTags).where(
                    and_(
                        models.ArticlesToTags.article_id == article_id,
                        ~models.ArticlesToTags.tag_id.in_(article_tag_ids),
                    )
                )
            )

        await session.flush()

        return await self.get_admin(session=session, slug=slug, language=language)

    async def delete(self, *, session: AsyncSession, slug: str) -> bool:
        await session.execute(delete(self.db_model).where(self.db_model.slug == slug))
        return True

    async def like(
        self,
        *,
        session: AsyncSession,
        slug: str,
        is_positive: bool = True,
        user_id: int,
    ) -> bool:
        article_query = select(self.db_model).where(self.db_model.slug == slug)
        article = (await session.execute(article_query)).scalar()
        if article is None:
            raise errors.ArticleNotFoundError()

        like = (
            await session.execute(
                select(models.ArticleLike).where(
                    and_(
                        models.ArticleLike.article_id == article.id,
                        models.ArticleLike.user_id == user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if like is None:
            like = models.ArticleLike(article_id=article.id, user_id=user_id, is_positive=is_positive)
        else:
            like.is_positive = is_positive

        session.add(like)
        session.add(article)
        await session.flush()
        await session.commit()
        return True

    async def delete_like(
        self,
        *,
        session: AsyncSession,
        slug: str,
        user_id: int,
    ) -> bool:
        article_query = select(self.db_model).where(self.db_model.slug == slug)
        article = (await session.execute(article_query)).scalar()
        if article is None:
            raise errors.ArticleNotFoundError()

        like = (
            await session.execute(
                select(models.ArticleLike).where(
                    and_(
                        models.ArticleLike.article_id == article.id,
                        models.ArticleLike.user_id == user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if like is None:
            return True

        session.add(article)
        await session.delete(like)
        await session.flush()
        await session.commit()
        return True

    async def get_root_comments(
        self,
        session: AsyncSession,
        article_id: int,
        pagination_body: schemas.PaginationBody,
    ) -> schemas.CommentsWithCount:
        query = (
            select(
                models.Comment.__table__,
                models.User.full_name.label("author"),
                coalesce(
                    func.sum(case((models.CommentLike.is_positive, 1), (~models.CommentLike.is_positive, -1), else_=0))
                ).label("likes"),
            )
            .select_from(
                models.Comment.__table__.join(
                    models.User.__table__,
                    models.Comment.author_id == models.User.id,
                ).join(models.CommentLike.__table__, models.CommentLike.comment_id == models.Comment.id, isouter=True)
            )
            .where(models.Comment.article_id == article_id)
            .group_by(
                models.Comment.id,
                models.Comment.article_id,
                models.Comment.author_id,
                models.Comment.content,
                models.Comment.parent_comment_id,
                models.Comment.created_at,
                models.Comment.updated_at,
                models.Comment.is_deleted,
                models.User.first_name,
                models.User.last_name,
            )
        )
        paginated_query = pagination.add_pagination_to_query(
            query=query, id_column=models.Comment.id, body=pagination_body
        )
        result = await session.execute(paginated_query)
        items = result.mappings().all()
        total_count = await self._get_rows_count_in(session=session, table=models.Comment)  # type: ignore
        return schemas.CommentsWithCount(items=items, count=total_count)

    async def get_comment_answers(
        self,
        session: AsyncSession,
        comment_id: int,
        pagination_body: schemas.PaginationBody,
    ) -> schemas.CommentsWithCount:
        query = (
            select(
                models.Comment.__table__,
                models.User.full_name.label("author"),
                coalesce(
                    func.sum(case((models.CommentLike.is_positive, 1), (~models.CommentLike.is_positive, -1), else_=0))
                ).label("likes"),
            )
            .select_from(
                self.db_model.__table__.join(
                    models.User.__table__,
                    models.Comment.author_id == models.User.id,
                ).join(models.CommentLike.__table__, models.CommentLike.comment_id == models.Comment.id, isouter=True)
            )
            .where(models.Comment.parent_comment_id == comment_id)
        )
        paginated_query = pagination.add_pagination_to_query(
            query=query, id_column=models.Comment.id, body=pagination_body
        )
        result = await session.execute(paginated_query)
        items = result.mappings().all()
        total_count = await self._get_rows_count_in(session=session, table=models.Comment)  # type: ignore
        return schemas.CommentsWithCount(items=items, count=total_count)

    @staticmethod
    async def create_comment(
        session: AsyncSession, article_id: int, author_id: int, item: schemas.CommentCreate
    ) -> schemas.Comment:
        result = models.Comment(article_id=article_id, author_id=author_id, **item.model_dump())
        session.add(result)
        await session.flush()

        return schemas.Comment.model_validate(result)

    @staticmethod
    async def update_comment(session: AsyncSession, comment_id: int, item: schemas.CommentUpdate) -> schemas.Comment:
        result = await session.get(models.Comment, comment_id)
        if result is None:
            raise errors.ArticleNotFoundError()

        result = await session.execute(
            update(models.Comment)
            .where(models.Comment.id == comment_id)
            .values(**item.model_dump())
            .returning(models.Comment)
        )
        return schemas.Comment.model_validate(result.first())

    @staticmethod
    async def delete_comment(session: AsyncSession, comment_id: int) -> None:
        result = await session.get(models.Comment, comment_id)
        if result is None:
            raise errors.ArticleCommentNotFoundError
        await session.execute(update(models.Comment).where(models.Comment.id == comment_id).values(is_deleted=True))

    @staticmethod
    async def get_comment_author_id(session: AsyncSession, comment_id: int) -> int:
        result = await session.execute(select(models.Comment.author_id).where(models.Comment.id == comment_id))
        author_id = result.scalars().first()
        if author_id is None:
            raise errors.ArticleCommentNotFoundError
        return author_id

    @staticmethod
    async def like_comment(
        session: AsyncSession,
        comment_id: int,
        user_id: int,
        is_positive: bool = True,
    ) -> bool:
        comment_query = select(models.Comment).where(models.Comment.id == comment_id)
        comment = (await session.execute(comment_query)).scalar()
        if comment is None:
            raise errors.ArticleCommentNotFoundError

        like = (
            await session.execute(
                select(models.CommentLike).where(
                    and_(
                        models.CommentLike.comment_id == comment.id,
                        models.CommentLike.user_id == user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if like is None:
            like = models.CommentLike(comment_id=comment.id, user_id=user_id, is_positive=is_positive)
        else:
            like.is_positive = is_positive

        session.add(like)
        session.add(comment)
        await session.flush()
        await session.commit()

    @staticmethod
    async def delete_comment_like(
        session: AsyncSession,
        comment_id: int,
        user_id: int,
    ) -> bool:
        comment_query = select(models.Comment).where(models.Comment.id == comment_id)
        comment = (await session.execute(comment_query)).scalar()
        if comment is None:
            raise errors.ArticleCommentNotFoundError

        like = (
            await session.execute(
                select(models.CommentLike).where(
                    and_(
                        models.CommentLike.comment_id == comment.id,
                        models.CommentLike.user_id == user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if like is None:
            return True

        session.add(comment)
        await session.delete(like)
        await session.flush()
        await session.commit()
        return True

    def _get_query(self, language: str) -> GenerativeSelect:
        generic_articles = self.db_model.__table__.alias("generic_articles")

        return (
            select(
                self.db_model.id,
                self.db_model.slug,
                self.db_model.title,
                self.db_model.subtitle,
                self.db_model.created_at,
                self.db_model.cover_image,
                models.User.full_name.label("author"),
                func.array_remove(array_agg(aggregate_order_by(models.Tag.name, models.Tag.name.desc())), None).label(
                    "tags"
                ),
                case(
                    (
                        generic_articles.c.language != None,  # noqa: E711
                        func.json_build_object(generic_articles.c.language, generic_articles.c.slug),
                    ),
                    else_=None,
                ).label("language_variants"),
                coalesce(
                    func.sum(case((models.ArticleLike.is_positive, 1), (~models.ArticleLike.is_positive, -1), else_=0))
                ).label("likes"),
            )
            .select_from(
                self.db_model.__table__.join(
                    models.ArticlesToTags.__table__.join(
                        models.Tag, models.ArticlesToTags.__table__.c.tag_id == models.Tag.id
                    ),
                    self.db_model.id == models.ArticlesToTags.__table__.c.article_id,
                    isouter=True,
                )
                .join(
                    generic_articles,
                    and_(
                        generic_articles.c.generic_id == models.Article.generic_id,
                        generic_articles.c.id != models.Article.id,
                    ),
                    isouter=True,
                )
                .join(models.User, models.User.id == self.db_model.author_id)
                .join(models.ArticleLike.__table__, models.ArticleLike.article_id == self.db_model.id, isouter=True)
            )
            .where(self.db_model.language == language)
            .group_by(
                self.db_model.id,
                models.User.first_name,
                models.User.last_name,
                generic_articles.c.language,
                generic_articles.c.slug,
            )
        )
