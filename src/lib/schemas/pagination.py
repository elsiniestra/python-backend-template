from typing import Generic

from fastapi import Query
from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo

from src.lib import enums, errors

from .base import BaseModelItemType


class PaginationBody(BaseModel):
    limit: int = Field(Query())
    page: int = Field(Query())
    offset_type: enums.OffsetType = Field(Query())
    offset_id: int | None = Field(Query(default=None))

    @field_validator("offset_id")
    def check_offset_id_nullable_violation(cls, offset_id: int | None, info: FieldValidationInfo) -> int | None:
        if offset_id is None and info.data.get("offset_type") not in [
            enums.OffsetType.FIRST,
            enums.OffsetType.SPECIFIC,
        ]:
            raise errors.OffsetIdNullableViolationError
        return offset_id

    @field_validator("offset_type")
    def check_offset_type_violation(cls, offset_type: enums.OffsetType, info: FieldValidationInfo) -> enums.OffsetType:
        if offset_type == enums.OffsetType.FIRST and info.data.get("page") != 1:
            raise errors.OffsetTypeViolationError
        return offset_type


class PaginationResponseUrlParams(BaseModel):
    prev_page_url_params: str | None = Field(default=None)
    next_page_url_params: str | None = Field(default=None)


class PaginationResponse(PaginationResponseUrlParams, Generic[BaseModelItemType]):
    items: list[BaseModelItemType]
    total_items: int
    total_pages: int | None = Field(default=None)
