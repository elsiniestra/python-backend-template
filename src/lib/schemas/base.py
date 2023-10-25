from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


class BaseModelORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseModelWithId(BaseModelORM):
    id: int


BaseModelItemType = TypeVar("BaseModelItemType", bound=BaseModelWithId)


class BaseModelWithCount(BaseModelORM, Generic[BaseModelItemType]):
    items: list[BaseModelItemType]
    count: int
