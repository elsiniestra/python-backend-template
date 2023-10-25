import abc
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx


class BaseService(abc.ABC):  # noqa: B024
    pass


class BaseAsyncWebService(BaseService):
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[httpx.AsyncClient, Any]:
        async with httpx.AsyncClient() as session:
            yield session
