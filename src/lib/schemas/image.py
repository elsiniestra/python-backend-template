from pydantic import BaseModel


class ImageResponse(BaseModel):
    tag: str
    url: str
