import glob
import os

from redis import asyncio as aioredis

from src.lib.errors import RGGraphAlreadyExistsError
from src.lib.utils.redisgraph.bulk_insert import bulk_insert


def create_redis_connection_pool(*, connection_url: str) -> aioredis.ConnectionPool:
    return aioredis.ConnectionPool.from_url(url=connection_url, db=0, encoding="utf-8", decode_responses=True)


async def sync_redis_graph(*, connection_url: str, graph_data_path: str) -> None:
    graphs: list[str] = next(os.walk(graph_data_path))[1]
    for graph in graphs:
        nodes = glob.glob(f"{graph_data_path}/{graph}/nodes/*.csv")
        relations = glob.glob(f"{graph_data_path}/{graph}/relationships/*.csv")
        try:
            await bulk_insert(connection_url=connection_url, graph=graph, nodes=nodes, relations=relations)
        except RGGraphAlreadyExistsError:
            pass  # TODO: Find the way to write the migrations correctly
            # await bulk_update(connection_url=connection_url, graph=graph, nodes=nodes, relations=relations)
