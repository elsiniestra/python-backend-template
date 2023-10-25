import argparse
import asyncio
import logging

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.config import create_settings
from src.core.persistence import create_new_pg_session_maker
from src.core.persistence.redis import create_redis_connection_pool
from src.domains import UserDomain, create_user_domain
from src.lib import schemas
from src.lib.logger import setup_logging

logger = logging.getLogger(__name__)


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI application for X Backend")

    parser.add_argument("--username", type=str, help="User login", default="admin")
    parser.add_argument("--first-name", type=str, help="User first name", default="Admin")
    parser.add_argument("--last-name", type=str, help="User last name", default="Adminovich")
    parser.add_argument("--email", type=str, help="User email", default="test@email.com")
    parser.add_argument("--password", type=str, help="User password", default="password")
    parser.add_argument("--role", type=str, help="User role", default=None)

    return parser


async def cli() -> None:
    # Settings
    settings = create_settings()

    # Setup logging
    setup_logging(path=settings.config_path.logger)

    # Parse arguments
    parser = get_argparser()
    args = parser.parse_args()
    logger.debug("Arguments: %s", args)

    pg_session_manager: async_sessionmaker[AsyncSession] = create_new_pg_session_maker(
        db_url=settings.db.pg_connection_url
    )
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    redis_connection_pool = create_redis_connection_pool(connection_url=settings.redis.connection_url)
    user_domain: UserDomain = create_user_domain(
        pg_session_manager=pg_session_manager,
        pwd_context=pwd_context,
        iam_graph_name=settings.redis.iam_graph_name,
        redis_connection_pool=redis_connection_pool,
    )
    user = await user_domain.controller.create(
        item=schemas.UserCreate(
            first_name=args.first_name,
            last_name=args.last_name,
            username=args.username,
            email=args.email,
            password=args.password,
        ),
    )
    if args.role:
        await user_domain.controller.assign_group(
            item_id=user.id,
            item=schemas.IAMGroupToUserAssign(
                user_group=args.role,
            ),
        )

    logger.info("User added")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cli())
