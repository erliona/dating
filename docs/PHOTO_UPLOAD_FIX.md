# Photo Upload Fix - sendData() Size Limit Issue

## Problem

Users were experiencing an error when submitting their profile form: **"Ошибка при создании анкеты. Попробуйте еще раз."** (Error creating profile. Try again.)

## Root Cause

### Telegram Mini App sendData() Limitation
The `Telegram.WebApp.sendData()` method has a strict **4096-byte (4KB) size limit** for the data string that can be sent to the bot.

### What Was Happening
The app was trying to send the complete profile data including 3 base64-encoded photos via `sendData()`:

```javascript
// OLD CODE (BROKEN)
const profileData = {
  name: "...",
  birth_date: "...",
  // ... other fields ...
  photos: [base64Photo1, base64Photo2, base64Photo3]  // ❌ PROBLEM!
};
tg.sendData(JSON.stringify({ action: 'create_profile', profile: profileData }));
```

### Why This Failed
Base64-encoded photos are extremely large:
- A typical compressed JPEG photo: **100-500KB** in base64
- With 3 photos: **300KB - 1.5MB** total payload
- This is **75x to 375x larger** than the 4KB limit!

Result: `sendData()` would throw an error, caught by the catch block, showing the generic error message.

## Solution

### Exclude Photos from sendData()
Only send profile **metadata** (without photos) via `sendData()`:

```javascript
// NEW CODE (FIXED)
const profileMetadata = {
  name: profileData.name,
  birth_date: profileData.birth_date,
  gender: profileData.gender,
  orientation: profileData.orientation,
  goal: profileData.goal,
  bio: profileData.bio,
  city: profileData.city,
  latitude: profileData.latitude,
  longitude: profileData.longitude,
  geohash: profileData.geohash,
  photo_count: profileData.photos.length  // ✓ Just the count, not the photos
};

const payload = {
  action: 'create_profile',
  profile: profileMetadata
};

tg.sendData(JSON.stringify(payload));  // ✓ Now only ~500 bytes
```

### Store Photos Locally (Temporary)
Photos are now stored in localStorage for temporary storage:

```javascript
localStorage.setItem('profile_data', JSON.stringify(profileData));  // Full data with photos
```

## Results

### Payload Size Comparison
| Method | Payload Size | Within 4KB Limit? |
|--------|-------------|-------------------|
| **Old** (with photos) | 300KB - 1.5MB | ❌ NO (75-375x too large) |
| **New** (metadata only) | ~500 bytes | ✅ YES (8x smaller than limit) |

### Testing
```bash
# Test payload size
node /tmp/test_payload_size.js
# Output: Payload size: 494 bytes ✓
```

## Future Work

### Phase 1: HTTP Photo Upload (Recommended)
Implement a dedicated HTTP API endpoint for photo uploads:

```javascript
// Upload photos separately via HTTP
async function uploadPhotos(photos, userId) {
  const formData = new FormData();
  photos.forEach((photo, index) => {
    formData.append(`photo${index}`, photo);
  });
  
  const response = await fetch('/api/upload-photos', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${initData}` },
    body: formData
  });
  
  return response.json();
}
```

### Phase 2: Progressive Upload
Show upload progress to users:
- Upload photos one by one
- Display progress bar
- Handle failures gracefully

### Phase 3: Image Optimization
Before upload:
- Resize images to maximum dimensions (e.g., 1200x1200)
- Compress to reduce file size
- Convert to WebP format for better compression

## References

- [Telegram Mini Apps Documentation](https://core.telegram.org/bots/webapps)
- `webapp/js/app.js` - Lines 892-946 (handleProfileSubmit function)
- `bot/main.py` - Lines 147-215 (handle_create_profile function)

## Related Issues

- Original bug report: See issue screenshot showing error message
- Fix commit: `513ce374e731dae6130d547da68d9c373141a664`
