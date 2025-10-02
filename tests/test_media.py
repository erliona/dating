"""Tests for media handling utilities."""

import base64

import pytest

from bot.media import (
    PhotoValidationError,
    decode_base64_photo,
    detect_mime_type,
    generate_photo_filename,
    validate_mime_type,
    validate_photo_size,
)


class TestValidatePhotoSize:
    """Tests for photo size validation."""
    
    def test_valid_photo_size(self):
        """Test valid photo size."""
        data = b"x" * (1024 * 1024)  # 1MB
        is_valid, error = validate_photo_size(data)
        assert is_valid is True
        assert error is None
    
    def test_photo_too_large(self):
        """Test photo exceeding max size."""
        data = b"x" * (6 * 1024 * 1024)  # 6MB
        is_valid, error = validate_photo_size(data)
        assert is_valid is False
        assert "5MB" in error
    
    def test_empty_photo(self):
        """Test empty photo data."""
        data = b""
        is_valid, error = validate_photo_size(data)
        assert is_valid is False
        assert "empty" in error.lower()


class TestDetectMimeType:
    """Tests for MIME type detection."""
    
    def test_detect_jpeg(self):
        """Test JPEG detection."""
        # JPEG magic bytes
        data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        mime_type = detect_mime_type(data)
        assert mime_type == "image/jpeg"
    
    def test_detect_png(self):
        """Test PNG detection."""
        # PNG magic bytes
        data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        mime_type = detect_mime_type(data)
        assert mime_type == "image/png"
    
    def test_detect_webp(self):
        """Test WebP detection."""
        # WebP magic bytes
        data = b'RIFF\x00\x00\x00\x00WEBP'
        mime_type = detect_mime_type(data)
        assert mime_type == "image/webp"
    
    def test_detect_unknown(self):
        """Test unknown file type."""
        data = b'unknown file format'
        mime_type = detect_mime_type(data)
        assert mime_type == "application/octet-stream"


class TestValidateMimeType:
    """Tests for MIME type validation."""
    
    def test_valid_jpeg(self):
        """Test valid JPEG MIME type."""
        is_valid, error = validate_mime_type("image/jpeg")
        assert is_valid is True
        assert error is None
    
    def test_valid_png(self):
        """Test valid PNG MIME type."""
        is_valid, error = validate_mime_type("image/png")
        assert is_valid is True
        assert error is None
    
    def test_valid_webp(self):
        """Test valid WebP MIME type."""
        is_valid, error = validate_mime_type("image/webp")
        assert is_valid is True
        assert error is None
    
    def test_invalid_mime_type(self):
        """Test invalid MIME type."""
        is_valid, error = validate_mime_type("application/pdf")
        assert is_valid is False
        assert "Invalid file type" in error


class TestDecodeBase64Photo:
    """Tests for base64 photo decoding."""
    
    def test_decode_simple_base64(self):
        """Test decoding simple base64."""
        data = b"test photo data"
        encoded = base64.b64encode(data).decode()
        decoded, error = decode_base64_photo(encoded)
        assert decoded == data
        assert error is None
    
    def test_decode_data_uri(self):
        """Test decoding base64 with data URI prefix."""
        data = b"test photo data"
        encoded = base64.b64encode(data).decode()
        data_uri = f"data:image/jpeg;base64,{encoded}"
        decoded, error = decode_base64_photo(data_uri)
        assert decoded == data
        assert error is None
    
    def test_decode_invalid_base64(self):
        """Test decoding invalid base64."""
        decoded, error = decode_base64_photo("invalid base64!!!")
        assert decoded is None
        assert error is not None
        assert "Failed to decode" in error


class TestGeneratePhotoFilename:
    """Tests for photo filename generation."""
    
    def test_generate_jpeg_filename(self):
        """Test JPEG filename generation."""
        filename = generate_photo_filename(123, "abcd1234efgh5678", "image/jpeg")
        assert filename.startswith("123_abcd1234efgh5678")
        assert filename.endswith(".jpg")
    
    def test_generate_png_filename(self):
        """Test PNG filename generation."""
        filename = generate_photo_filename(456, "1234567890abcdef", "image/png")
        assert filename.startswith("456_1234567890abcdef")
        assert filename.endswith(".png")
    
    def test_generate_webp_filename(self):
        """Test WebP filename generation."""
        filename = generate_photo_filename(789, "fedcba0987654321", "image/webp")
        assert filename.startswith("789_fedcba0987654321")
        assert filename.endswith(".webp")
    
    def test_filename_uniqueness(self):
        """Test that different hashes produce different filenames."""
        filename1 = generate_photo_filename(123, "hash1", "image/jpeg")
        filename2 = generate_photo_filename(123, "hash2", "image/jpeg")
        assert filename1 != filename2


class TestRemoveExifData:
    """Test EXIF data removal."""
    
    def test_remove_exif_placeholder(self):
        """Test EXIF removal placeholder implementation."""
        from bot.media import remove_exif_data
        
        # Create simple test data
        test_data = b"fake photo data"
        
        # Currently returns original data (placeholder)
        result = remove_exif_data(test_data)
        assert result == test_data
    
    def test_remove_exif_error_handling(self):
        """Test EXIF removal handles errors gracefully."""
        from bot.media import remove_exif_data
        
        # Test with empty data
        result = remove_exif_data(b"")
        assert result == b""


class TestCalculateNsfwScore:
    """Test NSFW score calculation."""
    
    def test_calculate_nsfw_score_placeholder(self):
        """Test NSFW detection placeholder implementation."""
        from bot.media import calculate_nsfw_score
        
        # Create simple test data
        test_data = b"fake photo data"
        
        # Currently returns 1.0 (safe) as placeholder
        score = calculate_nsfw_score(test_data)
        assert score == 1.0
        assert 0.0 <= score <= 1.0


class TestSavePhotoToStorage:
    """Test photo storage functionality."""
    
    def test_save_photo_to_storage(self, tmp_path):
        """Test saving photo to storage."""
        from bot.media import save_photo_to_storage
        import os
        
        # Create test data
        test_data = b"fake photo data"
        user_id = 123
        storage_path = str(tmp_path / "photos")
        
        # Save photo
        url = save_photo_to_storage(test_data, user_id, storage_path)
        
        # Verify URL format
        assert url.startswith("/photos/")
        assert url.endswith(".jpg")
        
        # Verify file was created
        filename = url.split("/")[-1]
        file_path = os.path.join(storage_path, filename)
        assert os.path.exists(file_path)
        
        # Verify content
        with open(file_path, 'rb') as f:
            saved_data = f.read()
        assert saved_data == test_data
    
    def test_save_photo_creates_directory(self, tmp_path):
        """Test that storage directory is created if it doesn't exist."""
        from bot.media import save_photo_to_storage
        import os
        
        test_data = b"fake photo data"
        storage_path = str(tmp_path / "nonexistent" / "photos")
        
        # Directory shouldn't exist yet
        assert not os.path.exists(storage_path)
        
        # Save photo
        url = save_photo_to_storage(test_data, 123, storage_path)
        
        # Directory should now exist
        assert os.path.exists(storage_path)


class TestValidateAndProcessPhoto:
    """Test photo validation and processing pipeline."""
    
    def test_validate_and_process_photo_success(self, tmp_path):
        """Test successful photo validation and processing."""
        from bot.media import validate_and_process_photo
        import base64
        
        # Create valid test photo data (small JPEG-like data)
        test_data = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100  # JPEG header + data
        base64_data = base64.b64encode(test_data).decode('utf-8')
        
        storage_path = str(tmp_path / "photos")
        
        # Process photo
        result = validate_and_process_photo(base64_data, 123, storage_path)
        
        # Verify result structure
        assert "url" in result
        assert "file_size" in result
        assert "mime_type" in result
        assert "safe_score" in result
        
        assert result["file_size"] > 0
        assert result["safe_score"] == 1.0  # Placeholder returns 1.0
    
    def test_validate_and_process_photo_invalid_base64(self, tmp_path):
        """Test processing with invalid base64 data."""
        from bot.media import validate_and_process_photo, PhotoValidationError
        
        storage_path = str(tmp_path / "photos")
        
        # Invalid base64
        with pytest.raises(PhotoValidationError):
            validate_and_process_photo("not-valid-base64!@#", 123, storage_path)
    
    def test_validate_and_process_photo_too_large(self, tmp_path):
        """Test processing photo that's too large."""
        from bot.media import validate_and_process_photo, PhotoValidationError, MAX_PHOTO_SIZE
        import base64
        
        # Create photo larger than max size
        large_data = b"\xFF\xD8\xFF\xE0" + b"\x00" * (MAX_PHOTO_SIZE + 1000)
        base64_data = base64.b64encode(large_data).decode('utf-8')
        
        storage_path = str(tmp_path / "photos")
        
        # Should raise validation error
        with pytest.raises(PhotoValidationError, match="exceeds maximum"):
            validate_and_process_photo(base64_data, 123, storage_path)
    
    def test_validate_and_process_photo_invalid_mime_type(self, tmp_path):
        """Test processing photo with invalid MIME type."""
        from bot.media import validate_and_process_photo, PhotoValidationError
        import base64
        
        # Create data that's not a valid image format (e.g., text)
        invalid_data = b"This is not an image file"
        base64_data = base64.b64encode(invalid_data).decode('utf-8')
        
        storage_path = str(tmp_path / "photos")
        
        # Should raise validation error
        with pytest.raises(PhotoValidationError, match="Invalid file type"):
            validate_and_process_photo(base64_data, 123, storage_path)
