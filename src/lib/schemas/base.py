from typing import Generic, TypeVar

from pydantic import BaseModel


class BaseModelORM(BaseModel):
    class Config:
        orm_mode = True


class BaseModelWithId(BaseModelORM):
    id: int


BaseModelItemType = TypeVar("BaseModelItemType", bound=BaseModelWithId)


class BaseModelWithCount(BaseModelORM, Generic[BaseModelItemType]):
    items: list[BaseModelItemType]
    count: int
