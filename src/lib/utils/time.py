import datetime
import time


def get_current_timestamp() -> int:
    return int(time.time())


def get_current_datetime() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%m %H:%M:%S")
