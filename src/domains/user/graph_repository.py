import abc
from typing import Any, Literal

from redis import asyncio as aioredis

from src.domains.base.repository import BaseGraphRepository
from src.lib.enums import IAMAccess, IAMScope, IAMUserGroup


class BaseUserGraphRepository(BaseGraphRepository, abc.ABC):
    @classmethod
    def create_instance(cls, connection_pool: aioredis.ConnectionPool, graph_name: str) -> "BaseUserGraphRepository":
        return cls(
            connection_pool=connection_pool,
            graph_name=graph_name,
        )

    @abc.abstractmethod
    async def assign_group_to_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> Literal[True]:
        ...

    @abc.abstractmethod
    async def unassign_group_from_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> None:
        ...

    @abc.abstractmethod
    async def is_user_granted_permission(
        self, session: "aioredis.Redis[Any]", user_id: int, scope: IAMScope, access: IAMAccess
    ) -> bool:
        ...


class UserGraphRepository(BaseUserGraphRepository):
    async def is_user_granted_permission(
        self, session: "aioredis.Redis[Any]", user_id: int, scope: IAMScope, access: IAMAccess
    ) -> bool:
        graph = self.get_graph(session=session)
        query = """
            MATCH (u:USER {id: %s})<-[:RELATES]->(:USERGROUP)-[:ALLOWS {access: %s}]->(:SCOPE {name: %s})
            RETURN EXISTS(u)
        """ % (
            user_id,
            access,
            scope,
        )
        result = await graph.query(q=query)
        return_value: bool = result.result_set[0]
        return return_value

    async def assign_group_to_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> Literal[True]:
        graph = self.get_graph(session=session)
        query = """
            MATCH (ug:USERGROUP {name: '%s'})
            MERGE (u:USER {id: %s})
            MERGE (u)-[e:RELATES]->(ug)
        """ % (
            user_id,
            user_group,
        )
        await graph.query(q=query)
        return True

    async def unassign_group_from_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> None:
        graph = self.get_graph(session=session)
        query = "MATCH (:USER {id: %s})<-[r:RELATES]->(:USERGROUP {name: '%s'}) DELETE f" % (user_id, user_group)
        await graph.query(q=query)
