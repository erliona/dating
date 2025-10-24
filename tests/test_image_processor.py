"""Tests for image processing pipeline."""

import pytest
import io
from PIL import Image
from services.media.image_processor import ImageProcessor


class TestImageProcessor:
    """Test image processing functionality."""
    
    def setup_method(self):
        """Setup test instance."""
        self.processor = ImageProcessor()
    
    def create_test_image(self, width: int = 100, height: int = 100, format: str = 'JPEG') -> bytes:
        """Create a test image."""
        image = Image.new('RGB', (width, height), color='red')
        output = io.BytesIO()
        image.save(output, format=format)
        return output.getvalue()
    
    def test_process_image_basic(self):
        """Test basic image processing."""
        image_data = self.create_test_image(800, 600)
        processed_data, thumbnail_data = self.processor.process_image(image_data)
        
        assert processed_data is not None
        assert thumbnail_data is not None
        assert len(processed_data) > 0
        assert len(thumbnail_data) > 0
    
    def test_process_image_large(self):
        """Test processing large image (should resize)."""
        image_data = self.create_test_image(3000, 2000)
        processed_data, thumbnail_data = self.processor.process_image(image_data)
        
        # Check that image was resized
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.width <= 1920
        assert processed_image.height <= 1920
    
    def test_process_image_small(self):
        """Test processing small image (should not resize)."""
        image_data = self.create_test_image(500, 400)
        processed_data, thumbnail_data = self.processor.process_image(image_data)
        
        # Check that image was not resized
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.width == 500
        assert processed_image.height == 400
    
    def test_thumbnail_creation(self):
        """Test thumbnail creation."""
        image_data = self.create_test_image(800, 600)
        processed_data, thumbnail_data = self.processor.process_image(image_data, create_thumbnail=True)
        
        assert thumbnail_data is not None
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        assert thumbnail_image.width <= 300
        assert thumbnail_image.height <= 300
    
    def test_no_thumbnail(self):
        """Test processing without thumbnail."""
        image_data = self.create_test_image(800, 600)
        processed_data, thumbnail_data = self.processor.process_image(image_data, create_thumbnail=False)
        
        assert processed_data is not None
        assert thumbnail_data is None
    
    def test_validate_image_valid(self):
        """Test valid image validation."""
        image_data = self.create_test_image(800, 600)
        assert self.processor.validate_image(image_data) is True
    
    def test_validate_image_too_small(self):
        """Test validation of too small image."""
        image_data = self.create_test_image(50, 50)
        assert self.processor.validate_image(image_data) is False
    
    def test_validate_image_too_large(self):
        """Test validation of too large image."""
        image_data = self.create_test_image(5000, 5000)
        assert self.processor.validate_image(image_data) is False
    
    def test_detect_nsfw_content_normal(self):
        """Test NSFW detection on normal image."""
        image_data = self.create_test_image(800, 600)
        assert self.processor.detect_nsfw_content(image_data) is False
    
    def test_detect_nsfw_content_extreme_ratio(self):
        """Test NSFW detection on extreme aspect ratio."""
        image_data = self.create_test_image(1000, 200)  # 5:1 ratio
        assert self.processor.detect_nsfw_content(image_data) is True
    
    def test_detect_nsfw_content_very_small(self):
        """Test NSFW detection on very small image."""
        image_data = self.create_test_image(100, 100)
        assert self.processor.detect_nsfw_content(image_data) is True
    
    def test_get_image_info(self):
        """Test getting image information."""
        image_data = self.create_test_image(800, 600)
        info = self.processor.get_image_info(image_data)
        
        assert 'width' in info
        assert 'height' in info
        assert 'format' in info
        assert info['width'] == 800
        assert info['height'] == 600
    
    def test_extract_exif_data(self):
        """Test EXIF data extraction."""
        image_data = self.create_test_image(800, 600)
        exif_data = self.processor.extract_exif_data(image_data)
        
        # Should return empty dict for test image (no EXIF)
        assert isinstance(exif_data, dict)
    
    def test_process_image_with_transparency(self):
        """Test processing image with transparency."""
        # Create RGBA image
        image = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
        output = io.BytesIO()
        image.save(output, format='PNG')
        image_data = output.getvalue()
        
        processed_data, thumbnail_data = self.processor.process_image(image_data)
        
        assert processed_data is not None
        assert thumbnail_data is not None
        
        # Check that transparency was handled (converted to RGB)
        processed_image = Image.open(io.BytesIO(processed_data))
        assert processed_image.mode == 'RGB'
    
    def test_process_image_unsupported_format(self):
        """Test processing unsupported format."""
        # Create a simple test image
        image = Image.new('RGB', (100, 100))
        output = io.BytesIO()
        image.save(output, format='BMP')  # Unsupported format
        image_data = output.getvalue()
        
        # Should fail validation
        assert self.processor.validate_image(image_data) is False
    
    def test_image_processing_error_handling(self):
        """Test error handling in image processing."""
        # Invalid image data
        invalid_data = b"not an image"
        
        with pytest.raises(Exception):
            self.processor.process_image(invalid_data)
    
    def test_thumbnail_quality(self):
        """Test thumbnail quality settings."""
        image_data = self.create_test_image(800, 600)
        processed_data, thumbnail_data = self.processor.process_image(image_data)
        
        # Thumbnail should be smaller than original
        assert len(thumbnail_data) < len(processed_data)
        
        # Check thumbnail dimensions
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        assert thumbnail_image.width <= 300
        assert thumbnail_image.height <= 300
