"""Telegram storage service implementation."""

import os
from pathlib import Path
from typing import BinaryIO, Optional

from core.interfaces import IStorageService


class TelegramStorageService(IStorageService):
    """Telegram implementation of storage service.

    Uses local filesystem storage (can be extended to use S3/CDN).
    """

    def __init__(self, storage_path: str, cdn_url: Optional[str] = None):
        """Initialize with storage configuration.

        Args:
            storage_path: Local path for file storage
            cdn_url: Optional CDN URL for serving files
        """
        self.storage_path = Path(storage_path)
        self.cdn_url = cdn_url

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def store_file(
        self, file_data: BinaryIO, file_name: str, content_type: str, user_id: int
    ) -> str:
        """Store a file and return its URL/path.

        Args:
            file_data: File binary data
            file_name: Original filename
            content_type: MIME type
            user_id: User who owns the file

        Returns:
            URL or path to the stored file
        """
        # Create user-specific directory
        user_dir = self.storage_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = user_dir / file_name
        with open(file_path, "wb") as f:
            f.write(file_data.read())

        # Return URL or path
        relative_path = f"{user_id}/{file_name}"
        if self.cdn_url:
            return f"{self.cdn_url}/{relative_path}"
        return relative_path

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a stored file."""
        if self.cdn_url:
            return f"{self.cdn_url}/{file_path}"
        return file_path

    async def delete_file(self, file_path: str) -> bool:
        """Delete a stored file."""
        try:
            full_path = self.storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        full_path = self.storage_path / file_path
        return full_path.exists()
