from .base import BadRequestError, NotFoundError, UnprocessableEntityError


class ArticleNotFoundError(NotFoundError):
    pass


class ArticleCommentNotFoundError(NotFoundError):
    pass


class OperationWithNonUserCommentError(BadRequestError):
    pass


class InvalidArticleListQueryError(UnprocessableEntityError):
    pass
