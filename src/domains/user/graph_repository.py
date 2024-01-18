from typing import Any, Literal

from redis import asyncio as aioredis

from src.core.base.repository import BaseGraphRepository
from src.lib.enums import IAMAccess, IAMScope, IAMUserGroup


class UserGraphRepository(BaseGraphRepository):
    async def is_user_granted_permission(
        self, session: "aioredis.Redis[Any]", user_id: int, scope: IAMScope, access: IAMAccess
    ) -> bool:
        graph = self.get_graph(session=session)
        query = """
            MATCH (u:USER {id: %s})<-[:RELATES]->(:USERGROUP)-[:ALLOWS {access: '%s'}]->(:SCOPE {name: '%s'})
            RETURN EXISTS(u)
        """ % (
            user_id,
            access,
            scope,
        )
        result = await graph.query(q=query)
        if not result.result_set:
            return False
        return_value: bool = result.result_set[0]
        return return_value

    async def get_user_groups(self, session: "aioredis.Redis[Any]", user_id: int) -> list[str]:
        graph = self.get_graph(session=session)
        query = """MATCH (:USER {id: %s})<-[r:RELATES]->(ug:USERGROUP) RETURN ug.name""" % (user_id,)
        result = await graph.query(q=query)
        return result.result_set[0] if result.result_set else []

    async def assign_group_to_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> Literal[True]:
        graph = self.get_graph(session=session)
        query = """
            MATCH (ug:USERGROUP {name: '%s'})
            MERGE (u:USER {id: %s})
            MERGE (u)-[e:RELATES]->(ug)
        """ % (
            user_group,
            user_id,
        )
        await graph.query(q=query)
        return True

    async def unassign_group_from_user(
        self, session: "aioredis.Redis[Any]", user_id: int, user_group: IAMUserGroup
    ) -> None:
        graph = self.get_graph(session=session)
        query = "MATCH (:USER {id: %s})<-[r:RELATES]->(:USERGROUP {name: '%s'}) DELETE r" % (user_id, user_group)
        await graph.query(q=query)
