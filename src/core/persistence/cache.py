from redis import asyncio as aioredis


def create_redis_connection_pool(*, connection_url: str) -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool.from_url(url=connection_url, db=0, encoding="utf-8", decode_responses=True)
