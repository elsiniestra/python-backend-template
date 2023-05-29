from pydantic import BaseModel, Field

from .base import BaseModelWithCount, BaseModelWithId
from .pagination import PaginationResponse


class ArticleCreate(BaseModel):
    title: str = Field(max_length=128)
    subtitle: str = Field(max_length=196)
    cover_image: str
    tags: list[str]
    author_id: int
    content: str


class InnerArticleCreate(ArticleCreate):
    slug: str = Field(max_length=196)


class ArticleShort(BaseModelWithId):
    title: str = Field(max_length=128)
    slug: str = Field(max_length=196)
    subtitle: str = Field(max_length=196)
    cover_image: str
    tags: list[str]
    created_at: int


class Article(ArticleShort):
    author: str
    content: str
    updated_at: int


class Comment(BaseModelWithId):
    author_username: str
    author_full_name: str | None
    content: str
    likes: int
    dislikes: int
    created_at: int
    updated_at: int


class CommentCreate(BaseModel):
    parent_comment_id: int
    content: str


class CommentUpdate(BaseModel):
    content: str


class CommentsWithCount(BaseModelWithCount[Comment]):
    items: list[Comment]


class CommentsPaginated(PaginationResponse[Comment]):
    items: list[Comment]


class ArticlesWithCount(BaseModelWithCount[ArticleShort]):
    items: list[ArticleShort]


class ArticlesPaginated(PaginationResponse[Article]):
    items: list[Article]
