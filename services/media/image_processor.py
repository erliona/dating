"""Image processing pipeline for media service."""

import io
import logging
from typing import Tuple, Optional
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing and optimization."""
    
    # Image size limits
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920
    THUMBNAIL_SIZE = (300, 300)
    
    # Quality settings
    JPEG_QUALITY = 85
    THUMBNAIL_QUALITY = 80
    
    def __init__(self):
        self.supported_formats = {'JPEG', 'PNG', 'WEBP'}
    
    def process_image(self, image_data: bytes, create_thumbnail: bool = True) -> Tuple[bytes, Optional[bytes]]:
        """
        Process image: resize, strip EXIF, optimize.
        
        Returns:
            Tuple of (processed_image_data, thumbnail_data)
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for JPEG output)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Strip EXIF data (privacy protection)
            image = self._strip_exif(image)
            
            # Resize if too large
            image = self._resize_image(image)
            
            # Optimize main image
            processed_data = self._optimize_image(image)
            
            # Create thumbnail if requested
            thumbnail_data = None
            if create_thumbnail:
                thumbnail = self._create_thumbnail(image)
                thumbnail_data = self._optimize_thumbnail(thumbnail)
            
            return processed_data, thumbnail_data
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise Exception(f"Failed to process image: {e}")
    
    def _strip_exif(self, image: Image.Image) -> Image.Image:
        """Remove EXIF data from image."""
        try:
            # Create new image without EXIF
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            return image_without_exif
        except Exception as e:
            logger.warning(f"Failed to strip EXIF: {e}")
            return image
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image if it's too large."""
        width, height = image.size
        
        if width <= self.MAX_WIDTH and height <= self.MAX_HEIGHT:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = min(self.MAX_WIDTH / width, self.MAX_HEIGHT / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create thumbnail image."""
        thumbnail = image.copy()
        thumbnail.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        return thumbnail
    
    def _optimize_image(self, image: Image.Image) -> bytes:
        """Optimize image for storage."""
        output = io.BytesIO()
        
        # Save as JPEG with optimization
        image.save(
            output,
            format='JPEG',
            quality=self.JPEG_QUALITY,
            optimize=True,
            progressive=True
        )
        
        return output.getvalue()
    
    def _optimize_thumbnail(self, image: Image.Image) -> bytes:
        """Optimize thumbnail for storage."""
        output = io.BytesIO()
        
        # Save thumbnail as JPEG
        image.save(
            output,
            format='JPEG',
            quality=self.THUMBNAIL_QUALITY,
            optimize=True
        )
        
        return output.getvalue()
    
    def get_image_info(self, image_data: bytes) -> dict:
        """Get image information."""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {}
    
    def validate_image(self, image_data: bytes) -> bool:
        """Validate image format and size."""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check format
            if image.format not in self.supported_formats:
                logger.warning(f"Unsupported format: {image.format}")
                return False
            
            # Check size (minimum 100x100, maximum 4000x4000)
            width, height = image.size
            if width < 100 or height < 100:
                logger.warning(f"Image too small: {width}x{height}")
                return False
            
            if width > 4000 or height > 4000:
                logger.warning(f"Image too large: {width}x{height}")
                return False
            
            # Check file size (max 10MB)
            if len(image_data) > 10 * 1024 * 1024:
                logger.warning(f"File too large: {len(image_data)} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def detect_nsfw_content(self, image_data: bytes) -> bool:
        """
        Basic NSFW detection (placeholder for AI model).
        
        TODO: Integrate with actual NSFW detection model
        """
        try:
            # Placeholder implementation
            # In production, this would use a trained model
            image = Image.open(io.BytesIO(image_data))
            
            # Basic heuristics (very simple)
            width, height = image.size
            aspect_ratio = width / height
            
            # Flag extreme aspect ratios as potentially problematic
            if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                logger.warning(f"Extreme aspect ratio detected: {aspect_ratio}")
                return True
            
            # Check for very small images (might be inappropriate)
            if width < 200 or height < 200:
                logger.warning(f"Very small image: {width}x{height}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"NSFW detection error: {e}")
            return True  # Err on the side of caution
    
    def extract_exif_data(self, image_data: bytes) -> dict:
        """Extract EXIF data before stripping (for logging)."""
        try:
            image = Image.open(io.BytesIO(image_data))
            exif_data = {}
            
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
            
            return exif_data
        except Exception as e:
            logger.error(f"Failed to extract EXIF: {e}")
            return {}


# Global image processor instance
image_processor = ImageProcessor()
