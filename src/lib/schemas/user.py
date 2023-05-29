from pydantic import BaseModel, Field, validator

from .base import BaseModelWithCount, BaseModelWithId
from .pagination import PaginationResponse


class UserBase(BaseModel):
    first_name: str | None = Field(max_length=32)
    last_name: str | None = Field(max_length=32)
    username: str = Field(max_length=32)
    email: str

    @validator("username")
    def lower_username(cls, username: str) -> str:
        return username.lower()


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    pass


class InnerUserCreate(UserBase):
    hashed_password: str


class User(UserBase, BaseModelWithId):
    pass


class UsersWithCount(BaseModelWithCount[User]):
    items: list[User]


class UsersPaginated(PaginationResponse[User]):
    items: list[User]


class UserIsGrantedPermissionResponse(BaseModel):
    valid: bool = Field(default=True)
