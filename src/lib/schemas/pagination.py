from pydantic import BaseModel, validator

from src.lib import enums, errors

from .base import BaseModelItemType, BaseModelWithCount


class PaginationBody(BaseModel):
    limit: int
    page: int
    offset_type: enums.OffsetType
    offset_id: int | None = None

    @validator("offset_id")
    def check_offset_id_nullable_violation(
        cls, offset_id: int | None, values: dict[str, int | enums.OffsetType]
    ) -> int | None:
        if offset_id is None and values.get("offset_type") not in [enums.OffsetType.FIRST, enums.OffsetType.SPECIFIC]:
            raise errors.OffsetIdNullableViolationError
        return offset_id

    @validator("offset_type")
    def check_offset_type_violation(
        cls, offset_type: enums.OffsetType, values: dict[str, int | enums.OffsetType]
    ) -> enums.OffsetType:
        if offset_type == enums.OffsetType.FIRST and values.get("page") != 1:
            raise errors.OffsetTypeViolationError
        return offset_type


class PaginationResponseUrlParams(BaseModel):
    prev_page_url_params: str | None
    next_page_url_params: str | None


class PaginationResponse(PaginationResponseUrlParams, BaseModelWithCount[BaseModelItemType]):
    items: list[BaseModelItemType]
    total_items: int
    total_pages: int
