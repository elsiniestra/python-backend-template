import functools
from typing import Any, Callable, Coroutine

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
        f"?limit={request_body.limit}&offset_id={items_first_id}"
        f"&offset_type={enums.OffsetType.PREV.value}&page={request_body.page - 1}"
    )
    next_page_params = (
        f"?limit={request_body.limit}&offset_id={items_last_id}"
        f"&offset_type={enums.OffsetType.NEXT.value}&page={request_body.page + 1}"
    )

    return schemas.PaginationResponseUrlParams(
        prev_page_url_params=prev_page_params if request_body.page > 1 else None,
        next_page_url_params=next_page_params if request_body.page < total_pages else None,
    )


def paginated(
    function: Callable[[Any], Coroutine[Any, Any, schemas.PaginationResponse[schemas.BaseModelWithId]]]
) -> Callable[
    [tuple[Any, ...], dict[str, Any]], Coroutine[Any, Any, schemas.PaginationResponse[schemas.BaseModelWithId]]
]:
    @functools.wraps(function)
    async def wrapper(*args, **kwargs) -> schemas.PaginationResponse:
        pagination_body = kwargs["pagination_body"]
        result: schemas.PaginationResponse[Any] = await function(*args, **kwargs)

        result.total_pages = int(result.total_items / pagination_body.limit)

        pagination_url_params = create_pagination_url_params(
            request_body=pagination_body,
            items_first_id=result.items[0].id if len(result.items) > 0 else None,
            items_last_id=result.items[-1].id if len(result.items) > 0 else None,
            total_pages=result.total_pages,
        )
        result.prev_page_url_params = pagination_url_params.prev_page_url_params
        result.next_page_url_params = pagination_url_params.next_page_url_params
        return result

    return wrapper
