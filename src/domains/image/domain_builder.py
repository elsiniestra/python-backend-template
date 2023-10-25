from dataclasses import dataclass

from botocore.client import BaseClient as S3Client

from src.domains.image.controller import ImageController
from src.domains.image.repository import ImageS3Repository


@dataclass(frozen=True)
class ImageDomain:
    controller: ImageController


def create_image_domain(*, s3_client: S3Client) -> ImageDomain:
    s3_repo = ImageS3Repository(session=s3_client)
    controller = ImageController(s3_repo=s3_repo)
    return ImageDomain(controller=controller)
