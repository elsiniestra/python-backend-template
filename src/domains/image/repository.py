import abc
import logging
import os

from botocore.exceptions import ClientError

from src.domains.base.repository import BaseS3Repository
from src.lib import schemas

logger = logging.getLogger(__name__)


class ImageS3Repository(BaseS3Repository, abc.ABC):
    def get_instance_url(self, *, bucket: schemas.S3Bucket, object_name: str, expiration: int = 3600) -> str | None:
        """Generate a pre-signed URL to share an S3 object

        :param bucket: string
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Pre-signed URL as string. If error, returns None.
        """
        try:
            response = self._session.generate_presigned_url(  # type: ignore
                "get_object", Params={"Bucket": bucket.name, "Key": object_name}, ExpiresIn=expiration
            )
        except ClientError as e:
            logger.error(e)
            return None

        return bucket.make_presigned_url(instance_url=response)

    def upload_file(self, file_name: str, bucket: schemas.S3Bucket, object_name: str | None = None) -> bool:
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        if object_name is None:
            object_name = os.path.basename(file_name)
        try:
            self._session.upload_file(file_name, bucket.name, object_name)  # type: ignore
        except ClientError as e:
            logger.error(e)
            return False
        return True
