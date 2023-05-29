from .base import BadRequestError, NotFoundError


class ArticleNotFoundError(NotFoundError):
    pass


class ArticleCommentNotFoundError(NotFoundError):
    pass


class OperationWithNonUserCommentError(BadRequestError):
    pass
