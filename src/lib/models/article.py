import typing

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.lib import utils

from .base import PgBaseModel
from .mixins import ReprMixin

if typing.TYPE_CHECKING:
    from .user import User, UserAuthor


articles_to_tags_table = Table(
    "articles_to_tags",
    PgBaseModel.metadata,
    Column("article_id", ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
    Column("tag_id", ForeignKey("tags.id"), nullable=False),
)


class Article(PgBaseModel, ReprMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(196), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(128), nullable=False)
    cover_image: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_authors.id"), nullable=False)
    author: "Mapped[UserAuthor]" = relationship("UserAuthor", lazy="joined")
    tags: "Mapped[list[Tag]]" = relationship(
        "Tag", secondary=articles_to_tags_table, back_populates="articles", lazy="joined"
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=utils.get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False, onupdate=utils.get_current_timestamp)


class Tag(PgBaseModel, ReprMixin):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    articles: "Mapped[list[Article]]" = relationship(
        "Article", secondary=articles_to_tags_table, back_populates="tags", lazy="joined"
    )


class Comment(PgBaseModel, ReprMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"), nullable=False)
    article: "Mapped[Article]" = relationship("Article", lazy="joined")
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    author: "Mapped[User]" = relationship("User", lazy="joined")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislikes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_comment_id: Mapped[int] = mapped_column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=utils.get_current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False, onupdate=utils.get_current_timestamp)
