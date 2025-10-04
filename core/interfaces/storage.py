"""Storage service interface - platform agnostic."""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class IStorageService(ABC):
    """Interface for file storage (photos, videos, etc.).
    
    Platform adapters can implement this using local storage, S3, CDN, etc.
    """
    
    @abstractmethod
    async def store_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str,
        user_id: int
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
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for a stored file."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a stored file."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass
