from src.lib.errors.base import BadRequestError, NotFoundError


class ImageNotFoundError(NotFoundError):
    pass


class NotSupportedImageMimeTypeError(BadRequestError):
    def __init__(self, detail: str = "Image type is not supported (supported: png, jpg/jpeg, webp)") -> None:
        super().__init__(detail=detail)
