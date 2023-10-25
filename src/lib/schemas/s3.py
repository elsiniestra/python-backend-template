from pydantic import BaseModel


class S3Bucket(BaseModel):
    name: str
    endpoint: str
    replace_domain: str | None = None

    def make_presigned_url(self, instance_url: str) -> str | None:
        if instance_url is not None and self.replace_domain is not None:
            return instance_url.replace(f"{self.endpoint}/{self.name}", self.replace_domain)
        return None
