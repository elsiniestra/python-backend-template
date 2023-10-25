from typing import Any, Literal

from pydantic import BaseModel, Field


class RequestJsonLog(BaseModel):
    type: Literal["request"] = Field(default="request")
    request_id: str
    request_method: str
    request_path: str
    request_query_params: dict[str, Any]
    request_referer: str | None = None
    request_body: str
    remote_ip: str
    remote_port: int


class ResponseJsonLog(BaseModel):
    type: Literal["response"] = Field(default="response")
    request_id: str
    response_status_code: int
    response_body: str
    response_duration: int


class ExceptionJsonLog(BaseModel):
    type: Literal["exception"] = Field(default="exception")
    request_id: str
    error: str
    traceback: str | None = None
