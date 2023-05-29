from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.domains.base.repository import BaseAsyncCrudRepository
from src.lib import errors, models, schemas
from src.lib.pagination import add_pagination_to_query
from src.lib.schemas import PaginationBody


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
    def create_instance(cls, session_manager: "sessionmaker[AsyncSession]") -> "ArticleDBRepository":
        return cls(
            session_manager=session_manager,
            db_model=models.Article,
            pydantic_model=schemas.Article,
            pydantic_model_with_count=schemas.ArticlesWithCount,
            pydantic_create_model=schemas.ArticleCreate,
            pydantic_update_model=schemas.ArticleCreate,
        )

    async def get_root_comments(
        self,
        session: AsyncSession,
        article_id: int,
        pagination_body: PaginationBody,
    ) -> schemas.CommentsWithCount:
        query = select(models.Comment).where(models.Comment.article_id == article_id)
        paginated_query = add_pagination_to_query(query=query, id_column=models.Comment.id, body=pagination_body)
        result = await session.execute(paginated_query)
        items = result.scalars().all()
        total_count = await self._get_rows_count_in(session=session, table=models.Comment)  # type: ignore
        return schemas.CommentsWithCount(items=items, count=total_count)

    async def get_comment_answers(
        self,
        session: AsyncSession,
        comment_id: int,
        pagination_body: PaginationBody,
    ) -> schemas.CommentsWithCount:
        query = select(models.Comment).where(models.Comment.parent_comment_id == comment_id)
        paginated_query = add_pagination_to_query(query=query, id_column=models.Comment.id, body=pagination_body)
        items = await session.execute(paginated_query)
        total_count = await self._get_rows_count_in(session=session, table=models.Comment)  # type: ignore
        return schemas.CommentsWithCount(items=items, count=total_count)

    async def create_comment(
        self, session: AsyncSession, article_id: int, author_id: int, item: schemas.CommentCreate
    ) -> schemas.Comment:
        result = models.Comment(article_id=article_id, author_id=author_id, **item.dict())
        session.add(result)
        await session.flush()
        return schemas.Comment.from_orm(result)

    async def update_comment(
        self, session: AsyncSession, comment_id: int, item: schemas.CommentUpdate
    ) -> schemas.Comment:
        result = await session.get(models.Comment, comment_id)
        if result is None:
            raise errors.NotFoundError()

        result = await session.execute(
            update(models.Comment)
            .where(models.Comment.id == comment_id)
            .values(**item.dict())
            .returning(models.Comment)
        )
        return schemas.Comment.from_orm(result.first())

    async def delete_comment(self, session: AsyncSession, comment_id: int) -> bool:
        result = await session.get(models.Comment, comment_id)
        if result is None:
            raise errors.ArticleCommentNotFoundError
        await session.delete(result)
        return True

    @staticmethod
    async def get_comment_author_id(session: AsyncSession, comment_id: int) -> int:
        result = await session.execute(select(models.Comment.author_id).where(models.Comment.id == comment_id))
        author_id_ans = result.scalars().first()
        if author_id_ans is None:
            raise errors.ArticleCommentNotFoundError
        author_id: int = author_id_ans
        return author_id
