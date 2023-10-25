import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.lib import enums

from .base import BaseModelORM, BaseModelWithCount, BaseModelWithId
from .pagination import PaginationResponse


class ArticleBase(BaseModel):
    title: str = Field(max_length=256)
    subtitle: str = Field(max_length=256)
    cover_image: str = Field(max_length=256)
    tags: list[str]


class ArticleCreate(ArticleBase):
    content: str
    author_id: int
    language: enums.LanguageType
    label: str = Field(max_length=32)
    generic_id: uuid.UUID | None = Field(description="If none, then new generic_id will be generated")
    is_main: bool = Field(default=False)


class ArticleUpdate(BaseModel):
    title: str | None = Field(max_length=256, default=None)
    subtitle: str | None = Field(max_length=256, default=None)
    label: str | None = Field(max_length=32, default=None)
    cover_image: str | None = Field(max_length=256, default=None)
    preview_image: str | None = Field(max_length=256, default=None)
    tags: list[str] | None = Field(default=None)
    author_id: int | None = Field(default=None)
    content: str | None = Field(default=None)
    language: enums.LanguageType | None = Field(default=None)
    generic_id: uuid.UUID | None = Field(default=None)
    is_draft: bool | None = Field(default=True)
    is_main: bool | None = Field(default=None)


class InnerArticleCreate(ArticleCreate):
    slug: str = Field(max_length=256)
    generic_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class ArticleCreateResponse(ArticleBase, BaseModelORM):
    author_id: int
    language: enums.LanguageType
    generic_id: uuid.UUID
    label: str = Field(max_length=32)
    slug: str = Field(max_length=256)
    created_at: int


class ArticleShort(ArticleBase, BaseModelWithId):
    slug: str = Field(max_length=256)
    author: str
    created_at: int
    likes: int
    language_variants: dict[enums.LanguageType, str] | None = Field(description="Map of language to slug", default=None)
    preview_image: str | None = Field(max_length=256, default=None)
    model_config = ConfigDict(use_enum_values=True)


class Article(ArticleShort):
    content: str
    updated_at: int | None = None


class ArticleShortEditor(ArticleShort):
    is_main: bool
    is_draft: bool


class ArticleEditor(ArticleShortEditor, Article):
    pass


class Comment(BaseModelWithId):
    author_username: str | None = None
    author_full_name: str | None = None
    is_deleted: bool = False
    likes: int = 0
    content: str
    created_at: int
    updated_at: int | None = None


class CommentCreate(BaseModel):
    parent_comment_id: int | None = Field(default=None, gt=0)
    content: str


class CommentUpdate(BaseModel):
    content: str


class CommentsWithCount(BaseModelWithCount[Comment]):
    items: list[Comment]


class CommentsPaginated(PaginationResponse[Comment]):
    items: list[Comment]


class ArticlesResponse(BaseModel):
    items: list[ArticleShort]


class ArticlesEditorResponse(BaseModel):
    items: list[ArticleShortEditor]


class ArticlesWithCount(ArticlesResponse, BaseModelWithCount[ArticleShort]):
    pass


class ArticlesPaginated(ArticlesResponse, PaginationResponse[Article]):
    pass


class ArticlesEditorWithCount(ArticlesEditorResponse, BaseModelWithCount[ArticleShortEditor]):
    pass


class ArticlesEditorPaginated(ArticlesEditorResponse, PaginationResponse[ArticleShortEditor]):
    pass
