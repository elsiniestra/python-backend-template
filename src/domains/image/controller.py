import os
import tempfile

from fastapi import Depends, Query, UploadFile
from slugify import slugify

from src.lib import errors, providers, schemas, utils

from .repository import ImageS3Repository


class ImageController:
    def __init__(self, s3_repo: ImageS3Repository) -> None:
        self._s3_repo = s3_repo

    async def get_file(
        self,
        tag: str = Query(min_length=20, max_length=32),
        bucket: schemas.S3Bucket = Depends(providers.get_s3_bucket_info),
    ) -> schemas.ImageResponse:
        url = self._s3_repo.get_instance_url(bucket=bucket, object_name=tag)
        if url is None:
            raise errors.ImageNotFoundError()
        return schemas.ImageResponse(tag=tag, url=url)

    async def upload_file_endpoint(
        self,
        file: UploadFile,
        bucket: schemas.S3Bucket = Depends(providers.get_s3_bucket_info),
    ) -> schemas.ImageResponse:
        types = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp"}

        if file.content_type not in types.keys():
            raise errors.NotSupportedImageMimeTypeError()

        tmp = tempfile.NamedTemporaryFile(suffix="." + types[file.content_type])
        name, extension = os.path.basename(file.filename).split(".")
        image_name = f"{slugify(f'{name} {utils.get_current_datetime()}')}.{extension}"
        content = await file.read()
        tmp.write(content)
        self._s3_repo.upload_file(file_name=tmp.name, bucket=bucket, object_name=image_name)
        url = self._s3_repo.get_instance_url(bucket=bucket, object_name=image_name)
        if url is None:
            raise errors.ImageNotFoundError()
        return schemas.ImageResponse(tag=image_name, url=url)
