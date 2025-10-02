# Photo Storage Configuration Guide

## Overview

The dating app now includes a robust photo storage system with support for both local storage and CDN integration. Photos are stored persistently on the server with automatic optimization and can be served either directly from the API server or via a CDN.

## Features

- **Persistent Storage**: Photos stored in Docker volume `/app/photos`
- **CDN Support**: Optional CDN URL configuration for production
- **Automatic Optimization**: Images resized and compressed (50-80% reduction)
- **Static File Serving**: Built-in photo serving when CDN not configured
- **Production Ready**: Designed for scalability and easy migration to CDN

## Architecture

### Without CDN (Default)

```
┌─────────────┐     Upload     ┌──────────────┐      Save      ┌─────────────┐
│   Client    │ ──────────────> │  API Server  │ ──────────────> │   Docker    │
│  (WebApp)   │                 │  (Port 8080) │                 │   Volume    │
└─────────────┘                 └──────────────┘                 └─────────────┘
                                       │                                │
                                       │  Serve from /photos/           │
                                       │  (Static file handler)         │
                                       └────────────────────────────────┘
```

### With CDN (Production)

```
┌─────────────┐     Upload     ┌──────────────┐      Save      ┌─────────────┐
│   Client    │ ──────────────> │  API Server  │ ──────────────> │   Docker    │
│  (WebApp)   │                 │  (Port 8080) │                 │   Volume    │
└─────────────┘                 └──────────────┘                 └─────────────┘
       │                               │                                │
       │ Fetch (via CDN URL)           │ Sync/Upload                    │
       ▼                               ▼                                ▼
┌─────────────┐                 ┌──────────────┐                 ┌─────────────┐
│     CDN     │ <───────────────│  CDN Sync    │ <───────────────│   Storage   │
│ (CloudFront)│                 │   Process    │                 │   (S3/etc)  │
└─────────────┘                 └──────────────┘                 └─────────────┘
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Photo Storage Path (inside container)
PHOTO_STORAGE_PATH=/app/photos

# Optional: CDN URL for serving photos
# Leave empty for local serving, set for production CDN
PHOTO_CDN_URL=

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8080
```

### Local Development (No CDN)

```bash
# .env
PHOTO_STORAGE_PATH=/app/photos
PHOTO_CDN_URL=
```

Photos will be:
- Stored in: Docker volume `photo_storage`
- Served from: `http://localhost:8080/photos/{filename}`

### Production with CDN

```bash
# .env
PHOTO_STORAGE_PATH=/app/photos
PHOTO_CDN_URL=https://cdn.example.com
```

Photos will be:
- Stored in: Docker volume `photo_storage`
- Served from: `https://cdn.example.com/{filename}`
- Synced to CDN via external process (see CDN Sync below)

## Docker Configuration

### docker-compose.yml

The photo storage volume is automatically configured:

```yaml
services:
  bot:
    volumes:
      - photo_storage:/app/photos
    ports:
      - "8080:8080"
    environment:
      PHOTO_STORAGE_PATH: /app/photos
      PHOTO_CDN_URL: ${PHOTO_CDN_URL:-}

volumes:
  photo_storage:
```

### Storage Location

Photos are stored in a persistent Docker volume:
- **Volume name**: `photo_storage`
- **Mount point**: `/app/photos` (inside container)
- **Host location**: Managed by Docker (typically `/var/lib/docker/volumes/`)

## Photo Upload Flow

### 1. Client Upload

```javascript
// Client-side (webapp/js/app.js)
const formData = new FormData();
formData.append('photo', file);
formData.append('slot_index', 0);

const response = await fetch(`${API_BASE_URL}/api/photos/upload`, {
  method: 'POST',
  headers: {
    'Authorization': `******
  },
  body: formData
});
```

### 2. Server Processing

```python
# Server-side (bot/api.py)
1. Authenticate request (JWT)
2. Validate photo (size, MIME type)
3. Optimize image (resize, compress)
4. Calculate NSFW score
5. Save to storage path
6. Generate photo URL
7. Return response
```

### 3. Photo URL Generation

```python
# Without CDN
photo_url = f"/photos/{filename}"  # Served by API server

# With CDN
photo_url = f"{config.photo_cdn_url}/{filename}"  # Served by CDN
```

## API Endpoints

### Upload Photo

**Endpoint**: `POST /api/photos/upload`

**Headers**:
```
Authorization: ******
Content-Type: multipart/form-data
```

**Body**:
- `photo` (file): Image file
- `slot_index` (int): Photo slot (0-2)

**Response**:
```json
{
  "url": "/photos/12345_0_abc123.jpg",
  "file_size": 524288,
  "optimized_size": 131072,
  "safe_score": 1.0,
  "message": "Photo uploaded successfully"
}
```

### Static Photo Serving (No CDN)

**Endpoint**: `GET /photos/{filename}`

**Example**:
```
GET http://localhost:8080/photos/12345_0_abc123.jpg
```

Returns the photo file with appropriate `Content-Type` header.

## CDN Integration

### Step 1: Configure CDN URL

```bash
# .env
PHOTO_CDN_URL=https://cdn.example.com
```

### Step 2: Set Up CDN Sync

Choose one of these approaches:

#### Option A: S3 + CloudFront

```bash
# Install AWS CLI
apt-get install awscli

# Sync photos to S3
aws s3 sync /var/lib/docker/volumes/photo_storage/_data s3://your-bucket/photos/

# Configure CloudFront distribution
# Point origin to S3 bucket
```

#### Option B: Periodic Rsync

```bash
# Create sync script
cat > /usr/local/bin/sync-photos.sh << 'EOF'
#!/bin/bash
rsync -av /var/lib/docker/volumes/photo_storage/_data/ cdn-server:/var/www/cdn/photos/
EOF

# Add to crontab
crontab -e
# */5 * * * * /usr/local/bin/sync-photos.sh
```

#### Option C: Docker Volume Mount

```yaml
# Mount photo storage to CDN server location
services:
  bot:
    volumes:
      - /var/www/cdn/photos:/app/photos
```

### Step 3: Configure CDN

**CloudFront Example**:
```
Origin Domain: your-bucket.s3.amazonaws.com
Origin Path: /photos
Behavior: Cache policy - CachingOptimized
```

**Cloudflare Example**:
```
DNS: cdn.example.com -> your-server-ip
Page Rule: cdn.example.com/photos/* - Cache Everything
```

## Storage Management

### Check Storage Usage

```bash
# Check Docker volume size
docker system df -v | grep photo_storage

# List photos in volume
docker run --rm -v photo_storage:/photos alpine ls -lh /photos/
```

### Backup Photos

```bash
# Backup to tar archive
docker run --rm -v photo_storage:/photos -v $(pwd):/backup \
  alpine tar czf /backup/photos-backup-$(date +%Y%m%d).tar.gz /photos/

# Restore from backup
docker run --rm -v photo_storage:/photos -v $(pwd):/backup \
  alpine tar xzf /backup/photos-backup-20241002.tar.gz -C /
```

### Clean Old Photos

```bash
# Remove photos older than 30 days
docker run --rm -v photo_storage:/photos alpine \
  find /photos -type f -mtime +30 -delete
```

## Security Considerations

### 1. Access Control

Photos are served:
- Through API server with authentication
- Or via CDN with proper access controls

### 2. NSFW Detection

All photos pass through NSFW detection:
```python
safe_score = calculate_nsfw_score(image_bytes)
if safe_score < 0.7:
    return error("Photo contains inappropriate content")
```

### 3. File Validation

- MIME type detection via magic bytes
- Size limits (5MB max)
- Format validation (JPEG, PNG, WebP only)

### 4. Secure Filenames

Photos saved with hash-based names:
```python
filename = f"{user_id}_{slot_index}_{hash[:16]}.{ext}"
# Example: 12345_0_a1b2c3d4e5f6g7h8.jpg
```

## Performance Optimization

### Image Optimization

All uploaded photos are automatically optimized:

```python
MAX_IMAGE_DIMENSION = 1200  # Max width/height
JPEG_QUALITY = 85           # Quality (0-100)
WEBP_QUALITY = 80
```

**Results**:
- 1500x1500 (500KB) → 1200x1200 (150KB) = 70% reduction
- 2000x1000 (600KB) → 1200x600 (120KB) = 80% reduction

### CDN Caching

When using CDN:
- Set long cache TTL (e.g., 1 year)
- Photos are immutable (hash-based names)
- Reduces server load
- Improves global delivery speed

### Static File Serving

Without CDN, API server uses efficient static file serving:
```python
app.router.add_static('/photos/', config.photo_storage_path, show_index=False)
```

## Monitoring

### Storage Metrics

Monitor photo storage:
- Volume size growth
- Upload success/failure rates
- Photo count per user
- Average file sizes

### API Metrics

Track upload performance:
- Upload latency
- Optimization time
- NSFW detection time
- Failed uploads

### CDN Metrics (if applicable)

- Cache hit ratio
- Origin requests
- Bandwidth usage
- Geographic distribution

## Troubleshooting

### Photos not saving

**Check permissions**:
```bash
docker exec dating-bot-1 ls -la /app/photos/
```

**Check volume mount**:
```bash
docker inspect dating-bot-1 | grep -A 5 "Mounts"
```

### Photos not serving

**Without CDN**: Check API server logs:
```bash
docker logs dating-bot-1 | grep "Static photo serving"
```

**With CDN**: Verify CDN sync:
```bash
# Check last sync time
ls -lh /var/lib/docker/volumes/photo_storage/_data/
```

### Storage full

**Check size**:
```bash
docker system df -v
```

**Clean up**:
```bash
# Remove old backups
find /backup -name "photos-backup-*.tar.gz" -mtime +7 -delete
```

## Migration Path

### From Local to CDN

1. **Configure CDN URL**:
   ```bash
   PHOTO_CDN_URL=https://cdn.example.com
   ```

2. **Sync existing photos**:
   ```bash
   aws s3 sync /var/lib/docker/volumes/photo_storage/_data s3://bucket/photos/
   ```

3. **Deploy update**:
   ```bash
   docker compose up -d
   ```

4. **Verify**: Check new uploads use CDN URLs

### From CDN back to Local

1. **Remove CDN URL**:
   ```bash
   PHOTO_CDN_URL=
   ```

2. **Deploy update**:
   ```bash
   docker compose up -d
   ```

3. **New uploads** use local serving automatically

## Best Practices

### Development

- Use local storage (no CDN)
- Regular backups before testing
- Monitor storage usage
- Test upload with various image formats

### Production

- Configure CDN for scalability
- Set up automated CDN sync
- Monitor storage and CDN metrics
- Implement photo retention policy
- Regular backups (automated)
- Load testing for peak usage

### Security

- Enable NSFW detection in production
- Use strong JWT secrets
- Implement rate limiting
- Monitor for unusual upload patterns
- Regular security scans

## Future Enhancements

### Planned

- [ ] Automatic S3 upload integration
- [ ] Photo thumbnail generation
- [ ] Image transformation API (resize on-the-fly)
- [ ] Photo moderation workflow
- [ ] User photo galleries
- [ ] Photo cropping/editing tools

### Possible

- [ ] Video support
- [ ] GIF optimization
- [ ] WebP conversion for all formats
- [ ] Progressive JPEG generation
- [ ] AI-based photo enhancement
- [ ] Duplicate photo detection

## Support

For issues or questions:
- Check logs: `docker logs dating-bot-1`
- Review configuration: `docker exec dating-bot-1 env | grep PHOTO`
- Test API: `curl http://localhost:8080/health`
- See [PHOTO_UPLOAD_API.md](./PHOTO_UPLOAD_API.md) for API details

## References

- [Photo Upload API Documentation](./PHOTO_UPLOAD_API.md)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [aiohttp Static Files](https://docs.aiohttp.org/en/stable/web_advanced.html#static-file-handling)
- [AWS S3 Sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)
- [CloudFront Setup](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html)
