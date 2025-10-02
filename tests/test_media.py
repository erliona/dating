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
