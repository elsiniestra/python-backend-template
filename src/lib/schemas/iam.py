from pydantic import BaseModel

from src.lib.enums import IAMUserGroup


class IAMGroupToUserAssign(BaseModel):
    user_group: IAMUserGroup
