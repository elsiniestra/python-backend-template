import uuid

from fastapi import Request

from src.core.config import TestSettings
from src.injected import DomainHolder
from src.lib import enums, schemas, utils


async def load_article(data: schemas.InnerArticleCreate, domain_holder: DomainHolder) -> schemas.ArticleCreateResponse:
    async with domain_holder.article.controller._db_repo.get_session() as session, session.begin():
        result = await domain_holder.article.controller._db_repo.create(session=session, item=data)
    return result


async def load_articles(domain_holder: DomainHolder, settings: TestSettings) -> None:
    generic_id = uuid.UUID("fe68c3ce-6cc7-4c35-8997-1dcd5e893d7a")
    article_1 = await load_article(
        data=schemas.InnerArticleCreate(
            title="Test Article",
            subtitle="Test Subtitle",
            slug=f"test-article-{utils.get_current_timestamp()}",
            label="News",
            cover_image="https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
            tags=["C", "B", "A"],
            author_id=1,
            content="Test text",
            language=enums.LanguageType.ENGLISH,
            generic_id=generic_id,
            is_main=True,
        ),
        domain_holder=domain_holder,
    )
    await domain_holder.article.controller.update(
        request=Request({"type": "http", "headers": []}),
        slug=article_1.slug,
        item=schemas.ArticleUpdate(is_draft=False),
    )
    article_2 = await load_article(
        data=schemas.InnerArticleCreate(
            title="Тест Статья",
            subtitle="Тест Подзаголовок",
            slug=f"test-statia-{utils.get_current_timestamp()}",
            label="Новости",
            cover_image="https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
            tags=["C", "B", "A"],
            author_id=1,
            content="Тест Текст",
            language=enums.LanguageType.RUSSIAN,
            generic_id=generic_id,
        ),
        domain_holder=domain_holder,
    )
    await domain_holder.article.controller.update(
        request=Request(
            {
                "type": "http",
                "headers": [("accept-language".encode(), "ru".encode())],
            }
        ),
        slug=article_2.slug,
        item=schemas.ArticleUpdate(is_draft=False),
    )

    await load_article(
        data=schemas.InnerArticleCreate(
            title="Test Draft Article",
            subtitle="Test Draft Subtitle",
            slug=f"test-draft-article-{utils.get_current_timestamp()}",
            label="Test News",
            cover_image="https://fastly.picsum.photos/id/866/1200/630.jpg?hmac=BSqxkAmM8i2PapPpt0U7OIUPfK8NVNcJSryob_QTeUA",
            tags=["C", "B", "A"],
            author_id=1,
            content="Test draft text",
            language=enums.LanguageType.ENGLISH,
            generic_id=uuid.uuid4(),
        ),
        domain_holder=domain_holder,
    )
