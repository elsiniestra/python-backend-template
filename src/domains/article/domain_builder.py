from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from .controller import ArticleController
from .repository import ArticleDBRepository


@dataclass(frozen=True)
class ArticleDomain:
    controller: ArticleController


def create_article_domain(*, pg_session_manager: "sessionmaker[AsyncSession]") -> ArticleDomain:
    db_repo = ArticleDBRepository.create_instance(session_manager=pg_session_manager)
    controller = ArticleController(db_repo=db_repo)
    return ArticleDomain(controller=controller)
