import boto3
from botocore.client import BaseClient
from botocore.client import Config as S3Config


def create_s3_client(*, region: str, endpoint: str, access_key: str, secret_key: str) -> BaseClient:
    return boto3.client(
        "s3",
        region_name=region,
        endpoint_url=f"https://{endpoint}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=S3Config(s3={"addressing_style": "virtual"}),
    )
