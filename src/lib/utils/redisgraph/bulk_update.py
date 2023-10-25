# TODO: CODE REVIEW AND REFACTOR
import abc
import csv
import logging
import pathlib

import redis
from redis import asyncio as aioredis

from src.lib.errors import RGConnectionError

logger = logging.getLogger(__name__)


def utf8len(s: str) -> int:
    return len(s.encode("utf-8"))


def quote_string(cell):
    cell = cell.strip()
    # Quote-interpolate cell if it is an unquoted string.
    try:
        float(cell)  # Check for numeric
    except ValueError:
        if (
            (cell.lower() != "false" and cell.lower() != "true")
            and (cell[0] != "[" and cell.lower != "]")  # Check for boolean
            and (cell[0] != '"' and cell[-1] != '"')  # Check for array
            and (cell[0] != "'" and cell[-1] != "'")  # Check for double-quoted string
        ):  # Check for single-quoted string
            cell = "".join(['"', cell, '"'])
    return cell


class BulkUpdate(abc.ABC):
    """Handler class for emitting bulk update commands"""

    def __init__(self, graph_name, filename, max_token_size, separator, variable_name, client):
        self.query = self._set_query(filename=filename, variable_name=variable_name, separator=separator)
        self.filename = filename
        self.separator = separator
        self.buffer_size = 0
        self.max_token_size = max_token_size * 1024 * 1024 - utf8len(self.query)
        self.graph = client.graph(graph_name)
        self.statistics = {}

    @staticmethod
    def _set_query(filename: str, variable_name: str, separator: str) -> str:
        basename: str = pathlib.Path(filename).stem
        with open(filename, "rt") as f:
            headers = next(f).split(separator)
            fields: str = ", ".join([f"{key.strip()}: row[{index}]" for index, key in enumerate(headers)])
            return " ".join(["UNWIND $rows AS", variable_name, "MERGE (:%s {%s})" % (basename, fields)])

    def _update_statistics(self, result):
        for key, new_val in result.statistics.items():
            self.statistics[key] = self.statistics.get(key, 0) + new_val

    async def _emit_buffer(self, rows):
        command = " ".join([rows, self.query])
        result = await self.graph.query(command)
        self._update_statistics(result)

    # Raise an exception if the query triggers a compile-time error
    async def _validate_query(self):
        command = " ".join(["CYPHER rows=[]", self.query])
        # The plan call will raise an error if the query is malformed or invalid.
        await self.graph.execution_plan(command)

    async def process_update_csv(self) -> None:
        await self._validate_query()

        with open(self.filename, "rt") as f:
            next(f)
            reader = csv.reader(
                f, delimiter=self.separator, skipinitialspace=True, quoting=csv.QUOTE_NONE, escapechar="\\"
            )

            rows_strs = []
            for row in reader:
                # Prepare the string representation of the current row.
                row = ",".join([quote_string(cell) for cell in row])
                next_line = "".join(["[", row.strip(), "]"])

                # Emit buffer now if the max token size would be exceeded by this addition.
                added_size = utf8len(next_line) + 1  # Add one to compensate for the added comma.
                if self.buffer_size + added_size > self.max_token_size:
                    # Concatenate all rows into a valid parameter set
                    buf = "".join(["CYPHER rows=[", ",".join(rows_strs), "]"])
                    await self._emit_buffer(buf)
                    rows_strs = []
                    self.buffer_size = 0

                # Concatenate the string into the rows string representation.
                rows_strs.append(next_line)
                self.buffer_size += added_size
            # Concatenate all rows into a valid parameter set
            buf = "".join(["CYPHER rows=[", ",".join(rows_strs), "]"])
            await self._emit_buffer(buf)


async def bulk_update(
    graph: str,
    connection_url: str,
    nodes: list[str],
    relations: list[str] | None = None,
    variable_name: str = "row",
    separator=",",
    max_token_size=500,
) -> None:
    """
    :param graph: Graph name
    :param connection_url: Redis connection url
    :param nodes: Path to node CSV input files
    :param relations: Path to relation CSV input files
    :param variable_name: Variable name for row array in queries (default: row)
    :param separator: Field token separator in CSV file
    :param max_token_size: Max size of each token in megabytes (default 500, max 512)
    :return: None
    """
    # Attempt to connect to Redis server
    if relations is None:
        relations = []
    try:
        client = aioredis.Redis.from_url(url=connection_url)
    except redis.exceptions.ConnectionError as e:
        msg = "Could not connect to Redis server. Exception: %s" % e
        logger.error(msg)
        raise RGConnectionError(msg)
    # Attempt to verify that RedisGraph module is loaded
    module_list = [m[b"name"] for m in await client.module_list()]
    if b"graph" not in module_list:
        msg = "RedisGraph module not loaded on connected server."
        logger.error(msg)
        raise RGConnectionError(msg)

    for node_name in nodes:
        await BulkUpdate(
            graph_name=graph,
            max_token_size=max_token_size,
            separator=separator,
            filename=node_name,
            variable_name=variable_name,
            client=client,
        ).process_update_csv()

    for relation_name in relations:
        await BulkUpdate(
            graph_name=graph,
            max_token_size=max_token_size,
            separator=separator,
            filename=relation_name,
            variable_name=variable_name,
            client=client,
        ).process_update_csv()
