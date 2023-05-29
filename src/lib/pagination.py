from typing import Any

from sqlalchemy import GenerativeSelect
from sqlalchemy.orm import InstrumentedAttribute

from src.lib import enums, schemas


def add_pagination_to_query(
    query: GenerativeSelect, id_column: InstrumentedAttribute[int], body: schemas.PaginationBody
) -> Any:
    statement: Any = query.limit(body.limit).order_by(id_column)
    if body.offset_type == enums.OffsetType.FIRST:
        return statement.order_by(id_column)
    if body.offset_type == enums.OffsetType.PREV:
        return statement.where(id_column < body.offset_id)
    if body.offset_type == enums.OffsetType.NEXT:
        return statement.where(id_column > body.offset_id)
    if body.offset_type == enums.OffsetType.SPECIFIC:
        return statement.slice((body.page - 1) * body.limit, body.page * body.limit)
    if body.offset_type == enums.OffsetType.LAST:
        return statement.where(id_column < body.offset_id)
    # the code will never get to this point, it is necessary to suppress the mypy error
    return query


def create_pagination_url_params(
    request_body: schemas.PaginationBody, items_first_id: int | None, items_last_id: int | None, total_pages: int
) -> schemas.PaginationResponseUrlParams:
    prev_page_params = (
        f"?limit={request_body.limit}&offset_id={items_first_id}&offset_type={enums.OffsetType.PREV.value}"
    )
    next_page_params = (
        f"?limit={request_body.limit}&offset_id={items_last_id}&offset_type={enums.OffsetType.NEXT.value}"
    )

    return schemas.PaginationResponseUrlParams(
        prev_page_url_params=prev_page_params if request_body.page > 1 else None,
        next_page_url_params=next_page_params if request_body.page < total_pages else None,
    )
