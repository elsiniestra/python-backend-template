class RedisGraphError(Exception):
    pass


class RGConnectionError(RedisGraphError):
    pass


class RGWrongCSVInputError(RedisGraphError):
    pass


class RGGraphAlreadyExistsError(RedisGraphError):
    pass


class RGCreateIndexError(RedisGraphError):
    pass
