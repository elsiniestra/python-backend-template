# TODO: CODE REVIEW AND REFACTOR
import logging

import redis
from redis import asyncio as aioredis

from src.lib.errors import (
    RGConnectionError,
    RGCreateIndexError,
    RGGraphAlreadyExistsError,
    RGWrongCSVInputError,
)
from src.lib.utils.redisgraph.config import Config
from src.lib.utils.redisgraph.label import Label
from src.lib.utils.redisgraph.query_buffer import QueryBuffer
from src.lib.utils.redisgraph.relation_type import RelationType

logger = logging.getLogger(__name__)


def parse_schemas(cls, query_buf, path_to_csv, csv_tuples, config):
    schemas = [None] * (len(path_to_csv) + len(csv_tuples))
    for idx, in_csv in enumerate(path_to_csv):
        # Build entity descriptor from input CSV
        schemas[idx] = cls(query_buf, in_csv, None, config)

    offset = len(path_to_csv)
    for idx, csv_tuple in enumerate(csv_tuples):
        # Build entity descriptor from input CSV
        schemas[idx + offset] = cls(query_buf, csv_tuple[1], csv_tuple[0], config)
    return schemas


# For each input file, validate contents and convert to binary format.
# If any buffer limits have been reached, flush all enqueued inserts to Redis.
def process_entities(entities):
    for entity in entities:
        entity.process_entities()
        added_size = entity.binary_size
        # Check to see if the addition of this data will exceed the buffer's capacity
        if (
            entity.query_buffer.buffer_size + added_size >= entity.config.max_buffer_size
            or entity.query_buffer.redis_token_count + len(entity.binary_entities) >= entity.config.max_token_count
        ):
            # Send and flush the buffer if appropriate
            entity.query_buffer.send_buffer()
        # Add binary data to list and update all counts
        entity.query_buffer.redis_token_count += len(entity.binary_entities)
        entity.query_buffer.buffer_size += added_size


async def bulk_insert(
    graph: str,
    nodes: list[str],
    connection_url: str,
    nodes_with_label: list[str] | None = None,
    separator: str = ",",
    relations: list[str] | None = None,
    relations_with_type: list[str] | None = None,
    enforce_schema: bool = False,
    quote: int = 0,
    id_type: str = "STRING",
    skip_invalid_nodes: bool = False,
    skip_invalid_edges: bool = False,
    escapechar: str = "\\",
    max_token_count: int = 1024,
    max_buffer_size: int = 64,
    max_token_size: int = 64,
    index: list[str] | None = None,
    full_text_index: list[str] | None = None,
) -> None:
    """
    :param graph: Graph name
    :param nodes: Path to node csv file
    :param connection_url: Redis connection url
    :param nodes_with_label: Label string followed by path to node csv file
    :param relations: Path to relation csv file
    :param relations_with_type: Relation type string followed by path to relation csv file
    :param separator: Field token separator in csv file
    :param enforce_schema: Enforce the schema described in CSV header rows
    :param id_type: The data type of unique node ID properties (either STRING or INTEGER)
    :param skip_invalid_nodes: Ignore nodes that use previously defined IDs
    :param skip_invalid_edges: Ignore invalid edges, print an error message and continue loading (True),
                               or stop loading after an edge loading failure (False)
    :param escapechar: The escape char used for the CSV reader (default \\). Use "none" for None
    :param quote: The quoting format used in the CSV file. QUOTE_MINIMAL=0,QUOTE_ALL=1,QUOTE_NONNUMERIC=2,QUOTE_NONE=3
    :param max_token_count: Max number of processed CSVs to send per query (default 1024)
    :param max_buffer_size: Max buffer size in megabytes (default 64, max 1024)
    :param max_token_size: Max size of each token in megabytes (default 64, max 512)
    :param index: Label:Propery on which to create an index
    :param full_text_index: Label:Propery on which to create an full text search index
    :return: None
    """
    if nodes_with_label is None:
        nodes_with_label = []
    if relations_with_type is None:
        relations_with_type = []
    if relations is None:
        relations = []
    if index is None:
        index = []
    if full_text_index is None:
        full_text_index = []
    if not (any(nodes) or any(nodes_with_label)):
        raise RGWrongCSVInputError("At least one node file must be specified.")

    # If relations are being built, we must store unique node identifiers to later resolve endpoints.
    store_node_identifiers = any(relations) or any(relations_with_type)

    # Initialize configurations with command-line arguments
    config = Config(
        max_token_count,
        max_buffer_size,
        max_token_size,
        enforce_schema,
        id_type,
        skip_invalid_nodes,
        skip_invalid_edges,
        separator,
        int(quote),
        store_node_identifiers,
        escapechar,
    )

    # Attempt to connect to Redis server
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

    # Verify that the graph name is not already used in the Redis database
    key_exists = await client.execute_command("EXISTS", graph)
    if key_exists:
        msg = "Graph with name '%s', could not be created, as Redis key '%s' already exists. Skip..." % (graph, graph)
        logger.info(msg)
        raise RGGraphAlreadyExistsError(msg)

    query_buf = QueryBuffer(graph, client, config)

    # Read the header rows of each input CSV and save its schema.
    labels = parse_schemas(Label, query_buf, nodes, nodes_with_label, config)
    reltypes = parse_schemas(RelationType, query_buf, relations, relations_with_type, config)
    process_entities(labels)
    process_entities(reltypes)

    # Send all remaining tokens to Redis
    await query_buf.send_buffer()
    await query_buf.wait_pool()

    # Add in Graph Indices after graph creation
    for i in index:
        l, p = i.split(":")
        try:
            await client.execute_command("GRAPH.QUERY", graph, "CREATE INDEX ON :%s(%s)" % (l, p))
        except redis.exceptions.ResponseError as e:
            msg = "Unable to create Index on Label: %s, Property: %s. Exception: %s" % (l, p, e)
            logger.error(msg)
            raise RGCreateIndexError(msg)

    # Add in Full Text Search Indices after graph creation
    for i in full_text_index:
        l, p = i.split(":")
        try:
            await client.execute_command(
                "GRAPH.QUERY", graph, "CALL db.idx.fulltext.createNodeIndex('%s', '%s')" % (l, p)
            )
        except redis.exceptions.ResponseError as e:
            msg = "Unknown Error: Unable to create Full Text Search Index on Label: %s, Property %s. Exception: %s" % (
                l,
                p,
                e,
            )
            logger.error(msg)
            raise RGCreateIndexError(msg)
