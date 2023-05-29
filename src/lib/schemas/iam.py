from pydantic import BaseModel

from src.lib.enums import IAMUserGroup


class IAMGroupToUserAssign(BaseModel):
    user_id: int
    user_group: IAMUserGroup
