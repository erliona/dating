# Image Processing Pipeline

## Overview

The image processing pipeline provides comprehensive image optimization, security validation, and content moderation for the dating platform.

## Features

### 1. Image Validation
- **Format Support**: JPEG, PNG, WEBP
- **Size Limits**: 100x100 to 4000x4000 pixels
- **File Size**: Maximum 10MB
- **Aspect Ratio**: Validates reasonable proportions

### 2. Security Processing
- **EXIF Stripping**: Removes all metadata (location, camera info, etc.)
- **Format Standardization**: All images converted to JPEG
- **Quality Optimization**: 85% quality for main images, 80% for thumbnails

### 3. Image Optimization
- **Resize**: Maximum 1920x1920 pixels
- **Thumbnail Generation**: 300x300 pixels
- **Progressive JPEG**: Better loading experience
- **Compression**: Optimized file sizes

### 4. Content Moderation
- **NSFW Detection**: Basic heuristics (extensible to AI models)
- **Aspect Ratio Analysis**: Flags extreme ratios
- **Size Analysis**: Detects suspiciously small images

## Implementation

### ImageProcessor Class

```python
class ImageProcessor:
    # Configuration
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920
    THUMBNAIL_SIZE = (300, 300)
    JPEG_QUALITY = 85
    THUMBNAIL_QUALITY = 80
    
    def process_image(self, image_data: bytes, create_thumbnail: bool = True) -> Tuple[bytes, Optional[bytes]]
    def validate_image(self, image_data: bytes) -> bool
    def detect_nsfw_content(self, image_data: bytes) -> bool
    def extract_exif_data(self, image_data: bytes) -> dict
    def get_image_info(self, image_data: bytes) -> dict
```

### Processing Pipeline

1. **Validation**
   ```python
   if not image_processor.validate_image(file_data):
       return error_response("Invalid image format or size")
   ```

2. **NSFW Detection**
   ```python
   if image_processor.detect_nsfw_content(file_data):
       return error_response("Content not allowed")
   ```

3. **EXIF Extraction** (for logging)
   ```python
   exif_data = image_processor.extract_exif_data(file_data)
   logger.info(f"EXIF data extracted: {list(exif_data.keys())}")
   ```

4. **Processing**
   ```python
   processed_data, thumbnail_data = image_processor.process_image(file_data, create_thumbnail=True)
   ```

5. **Storage**
   ```python
   # Upload main image
   await minio_client.upload_file("photos", object_name, processed_data)
   
   # Upload thumbnail
   if thumbnail_data:
       await minio_client.upload_file("thumbnails", thumbnail_name, thumbnail_data)
   ```

## Security Features

### EXIF Data Removal
- **Privacy Protection**: Removes location data, camera settings, timestamps
- **Metadata Stripping**: Eliminates all EXIF tags
- **Clean Images**: Only image data remains

### Content Validation
- **Format Verification**: Ensures valid image formats
- **Size Validation**: Prevents oversized images
- **Content Analysis**: Basic NSFW detection

### File Security
- **Path Traversal Prevention**: Sanitized filenames
- **Size Limits**: Prevents DoS attacks
- **Type Validation**: MIME type verification

## Performance Optimization

### Image Resizing
- **Smart Resizing**: Maintains aspect ratio
- **Quality Preservation**: High-quality resampling
- **Efficient Processing**: LANCZOS algorithm

### Thumbnail Generation
- **Fast Loading**: 300x300 thumbnails for discovery
- **Optimized Storage**: Separate thumbnail bucket
- **CDN Ready**: Optimized for content delivery

### Compression
- **Progressive JPEG**: Better user experience
- **Quality Balance**: 85% quality vs file size
- **Optimization**: Automatic compression

## Storage Strategy

### MinIO Buckets
- **photos**: Full-size processed images
- **thumbnails**: 300x300 thumbnails
- **verification**: Profile verification images

### File Naming
- **UUID-based**: Secure, unique filenames
- **Extension Preservation**: Maintains file type
- **Organized Structure**: Logical bucket organization

## Monitoring & Metrics

### Processing Metrics
- **Processing Time**: Track image processing duration
- **Success Rate**: Monitor processing success
- **Error Types**: Categorize processing failures

### Security Metrics
- **NSFW Detection**: Track flagged content
- **EXIF Stripping**: Monitor metadata removal
- **Validation Failures**: Track invalid uploads

### Storage Metrics
- **File Sizes**: Monitor storage usage
- **Thumbnail Generation**: Track thumbnail creation
- **Upload Success**: Monitor upload completion

## Error Handling

### Validation Errors
```json
{
  "error": "Invalid image format or size",
  "code": "INVALID_IMAGE"
}
```

### NSFW Detection
```json
{
  "error": "Content not allowed",
  "code": "NSFW_DETECTED"
}
```

### Processing Errors
```json
{
  "error": "Image processing failed",
  "code": "PROCESSING_ERROR"
}
```

## Testing

### Unit Tests
- **Image Validation**: Test various image formats and sizes
- **Processing Pipeline**: Test resize, thumbnail, optimization
- **Security Features**: Test EXIF stripping, NSFW detection
- **Error Handling**: Test invalid inputs and edge cases

### Integration Tests
- **MinIO Integration**: Test upload/download functionality
- **End-to-End**: Test complete upload workflow
- **Performance**: Test with large images

## Future Enhancements

### AI-Powered Features
- **Advanced NSFW Detection**: Machine learning models
- **Content Classification**: Automatic content tagging
- **Quality Assessment**: Image quality scoring

### Performance Improvements
- **Async Processing**: Background image processing
- **Caching**: Redis-based thumbnail caching
- **CDN Integration**: Automatic CDN distribution

### Security Enhancements
- **Watermarking**: Invisible watermarking for protection
- **Deepfake Detection**: AI-based authenticity verification
- **Advanced Metadata**: Enhanced EXIF analysis

## Configuration

### Environment Variables
```bash
# Image processing settings
MAX_IMAGE_WIDTH=1920
MAX_IMAGE_HEIGHT=1920
THUMBNAIL_SIZE=300
JPEG_QUALITY=85
THUMBNAIL_QUALITY=80

# MinIO settings
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=dating
MINIO_ROOT_PASSWORD=dating123
```

### Docker Configuration
```yaml
media-service:
  environment:
    - MINIO_ENDPOINT=http://minio:9000
    - MINIO_ROOT_USER=${MINIO_ROOT_USER}
    - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
  depends_on:
    - minio
```

## Best Practices

1. **Always Validate**: Check image format and size before processing
2. **Strip EXIF**: Remove all metadata for privacy
3. **Generate Thumbnails**: Create optimized thumbnails for discovery
4. **Monitor Performance**: Track processing times and success rates
5. **Handle Errors**: Graceful error handling for all edge cases
6. **Test Thoroughly**: Comprehensive testing of all image types
7. **Document Changes**: Keep documentation updated with new features
