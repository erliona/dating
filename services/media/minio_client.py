"""MinIO S3 client for media service."""

import logging
import os

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO S3-compatible client wrapper."""

    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ROOT_USER", "dating"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "dating123"),
            secure=False,  # Use HTTP for internal communication
        )
        self.buckets = {
            "photos": "photos",
            "thumbnails": "thumbnails",
            "verification": "verification",
        }

    async def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file to MinIO bucket."""
        try:
            from io import BytesIO

            bucket_name = self.buckets.get(bucket, bucket)
            file_obj = BytesIO(file_data)

            # Upload file
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_obj,
                length=len(file_data),
                content_type=content_type,
            )

            logger.info(f"File uploaded to MinIO: {bucket_name}/{object_name}")
            return f"{bucket_name}/{object_name}"

        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise Exception(f"Failed to upload file: {e}") from e

    async def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download file from MinIO bucket."""
        try:
            bucket_name = self.buckets.get(bucket, bucket)

            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            return data

        except S3Error as e:
            logger.error(f"MinIO download error: {e}")
            raise Exception(f"Failed to download file: {e}") from e

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """Delete file from MinIO bucket."""
        try:
            bucket_name = self.buckets.get(bucket, bucket)

            self.client.remove_object(bucket_name, object_name)

            logger.info(f"File deleted from MinIO: {bucket_name}/{object_name}")
            return True

        except S3Error as e:
            logger.error(f"MinIO delete error: {e}")
            return False

    async def file_exists(self, bucket: str, object_name: str) -> bool:
        """Check if file exists in MinIO bucket."""
        try:
            bucket_name = self.buckets.get(bucket, bucket)

            self.client.stat_object(bucket_name, object_name)
            return True

        except S3Error:
            return False

    def get_file_url(self, bucket: str, object_name: str) -> str:
        """Get public URL for file."""
        bucket_name = self.buckets.get(bucket, bucket)
        return f"/media/{bucket_name}/{object_name}"


# Global MinIO client instance
minio_client = MinIOClient()
