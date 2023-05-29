from typing import Any

from pydantic import BaseModel, Field


class RequestJsonLog(BaseModel):
    type: str = Field(const=True, default="request")
    request_id: str
    request_method: str
    request_path: str
    request_query_params: dict[str, Any]
    request_referer: str | None
    request_body: str
    remote_ip: str
    remote_port: int


class ResponseJsonLog(BaseModel):
    type: str = Field(const=True, default="response")
    request_id: str
    response_status_code: int
    response_body: str
    response_duration: int


class ExceptionJsonLog(BaseModel):
    type: str = Field(const=True, default="exception")
    request_id: str
    error: str
    traceback: str | None
