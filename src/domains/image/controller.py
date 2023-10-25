import os
import tempfile
from typing import Annotated

from fastapi import File, Form, Query, UploadFile
from slugify import slugify

from src.lib import errors, providers, schemas, utils

from .repository import ImageS3Repository


class ImageController:
    def __init__(self, s3_repo: ImageS3Repository) -> None:
        self._s3_repo = s3_repo

    async def get_file(
        self,
        tag: Annotated[str, Query()],
        settings: providers.MainSettingsRequired,
    ) -> schemas.ImageResponse:
        url = self._s3_repo.get_instance_url(
            object_name=tag,
            bucket=schemas.S3Bucket(
                name=settings.s3.bucket, endpoint=settings.s3.endpoint, replace_domain=settings.s3.replace_domain
            ),
        )
        if url is None:
            raise errors.ImageNotFoundError()
        return schemas.ImageResponse(tag=tag, url=url)

    async def upload_file_endpoint(
        self,
        file: Annotated[UploadFile, File()],
        folder: Annotated[str, Form()],
        settings: providers.MainSettingsRequired,
    ) -> schemas.ImageResponse:
        types = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp"}

        if file.content_type not in types.keys():
            raise errors.NotSupportedImageMimeTypeError()

        tmp = tempfile.NamedTemporaryFile(suffix="." + types[file.content_type])
        name, extension = os.path.basename(file.filename).split(".")
        image_name = f"{folder}/{slugify(f'{name} {utils.get_current_datetime()}')}.{extension}"
        content = await file.read()
        tmp.write(content)
        bucket = schemas.S3Bucket(
            name=settings.s3.bucket, endpoint=settings.s3.endpoint, replace_domain=settings.s3.replace_domain
        )
        self._s3_repo.upload_file(file_name=tmp.name, bucket=bucket, object_name=image_name)
        url = self._s3_repo.get_instance_url(bucket=bucket, object_name=image_name)
        if url is None:
            raise errors.ImageNotFoundError()
        return schemas.ImageResponse(tag=image_name, url=url)
