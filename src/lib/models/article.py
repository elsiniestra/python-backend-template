import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.lib import enums, utils

from .base import PgBaseModel
from .mixins import PKMixin, ReprMixin


class ArticlesToTags(PgBaseModel):
    __tablename__ = "articles_to_tags"
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    __table_args__ = (PrimaryKeyConstraint("tag_id", "article_id", name="_tag_article_ids_key"),)


class Article(PgBaseModel, PKMixin, ReprMixin):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    label: Mapped[str] = mapped_column(String(32), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(256), nullable=False)
    cover_image: Mapped[str] = mapped_column(String(256), nullable=False)
    preview_image: Mapped[str] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=utils.get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=True, onupdate=utils.get_current_timestamp)
    language: Mapped[enums.LanguageType] = mapped_column(
        Enum(enums.LanguageType, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generic_id: Mapped[int] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    """Generic article ID.

    This ID is used to link articles in different languages together.

    Like we have an article with ID 1 in English and an article with ID 2 in Russian
    (which is the same article, but in Russian),
    then we set generic_id to unique ID for this articles (for example, 1).

    This way we can easily get all articles about the same topic in different languages.

    ```
    Article(id: 1, title: "Hello world", lang: en, generic_id: 1)
    Article(id: 2, title: "Привет мир", lang: ru, generic_id: 1)
    ```
    """


class Tag(PgBaseModel, PKMixin, ReprMixin):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)


class Comment(PgBaseModel, PKMixin, ReprMixin):
    __tablename__ = "comments"

    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    """Total amount of likes for this comment minus dislikes."""
    parent_comment_id: Mapped[int] = mapped_column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=utils.get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=True, onupdate=utils.get_current_timestamp)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class BaseLike(PgBaseModel, ReprMixin):
    __abstract__ = True

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, primary_key=True)
    is_positive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=utils.get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=True, onupdate=utils.get_current_timestamp)


class ArticleLike(BaseLike):
    __tablename__ = "article_likes"
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"), nullable=False, primary_key=True)


class CommentLike(BaseLike):
    __tablename__ = "comment_likes"
    comment_id: Mapped[int] = mapped_column(Integer, ForeignKey("comments.id"), nullable=False, primary_key=True)
