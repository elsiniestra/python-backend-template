from .base import BadRequestError


class OffsetIdNullableViolationError(BadRequestError):
    def __init__(self, detail: str = "Offset ID cannot be empty if offset type is FIRST or SPECIFIC") -> None:
        super().__init__(detail=detail)


class OffsetTypeViolationError(BadRequestError):
    def __init__(self, detail: str = "Offset type provided incorrectly according to another fields.") -> None:
        super().__init__(detail=detail)
