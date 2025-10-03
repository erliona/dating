# Bug Fixes - Issues #1, #2, #3

This document describes the fixes implemented for three reported issues in the dating app.

## Overview

- **Issue #1**: Success screen showing when database is empty ✅ FIXED
- **Issue #2**: Grafana panels not appearing ✅ ALREADY FIXED (verified)
- **Issue #3**: App version missing from profile form and success screen ✅ FIXED

---

## Issue #1: Profile Check Shows "Анкета создана!" When Database is Empty

### Problem Description

The application was showing the success screen ("Анкета создана!") even when the database had no records in the `users` or `profiles` tables. This occurred because the app only checked `localStorage` to determine if a profile existed, without verifying the actual database state.

**Scenario**:
1. User creates a profile (localStorage is set to `profile_created: true`)
2. Developer resets the database
3. User reopens the app
4. ❌ App shows "Анкета создана!" even though database is empty

### Root Cause

The `checkUserProfile()` function in `webapp/js/app.js` only checked `localStorage`:

```javascript
// OLD CODE (Problem)
async function checkUserProfile() {
  const profileCreated = localStorage.getItem('profile_created') === 'true';
  return profileCreated; // ❌ No database verification
}
```

### Solution Implemented

1. **Added Backend API Endpoint** (`/api/profile/check`)
   - Location: `bot/api.py`
   - Endpoint: `GET /api/profile/check?user_id={user_id}`
   - Returns: `{"has_profile": true/false, "user_id": 12345}`
   - Queries PostgreSQL database for actual profile existence

2. **Enhanced Frontend Logic**
   - Location: `webapp/js/app.js` 
   - Modified `checkUserProfile()` function to:
     - Check localStorage first (fast path)
     - Verify with backend API
     - Clear stale localStorage if database doesn't have profile
     - Handle API failures gracefully

3. **Added Comprehensive Tests**
   - Location: `tests/test_api.py`
   - 4 new test cases:
     - `test_check_profile_exists` - Verify positive case
     - `test_check_profile_not_exists` - Verify negative case
     - `test_check_profile_missing_user_id` - Error handling
     - `test_check_profile_invalid_user_id` - Validation

### Technical Details

**New API Endpoint**:
```python
async def check_profile_handler(request: web.Request) -> web.Response:
    """Check if user has a profile in the database."""
    user_id = int(request.query.get("user_id"))
    
    async with session_maker() as session:
        repository = ProfileRepository(session)
        user = await repository.get_user_by_tg_id(user_id)
        
        if not user:
            return web.json_response({"has_profile": False, "user_id": user_id})
        
        profile = await repository.get_profile_by_user_id(user.id)
        return web.json_response({
            "has_profile": profile is not None,
            "user_id": user_id
        })
```

**Enhanced Frontend Check**:
```javascript
async function checkUserProfile() {
  const currentUserId = tg?.initDataUnsafe?.user?.id;
  const profileCreated = localStorage.getItem('profile_created') === 'true';
  
  // Verify with backend API
  const response = await fetch(`${API_BASE_URL}/api/profile/check?user_id=${currentUserId}`);
  const data = await response.json();
  
  // Clear localStorage if database doesn't have profile
  if (profileCreated && !data.has_profile) {
    console.log('Profile not found in database, clearing localStorage');
    localStorage.removeItem('profile_created');
    localStorage.removeItem('profile_data');
    localStorage.removeItem('profile_user_id');
    return false;
  }
  
  return data.has_profile;
}
```

### Testing

**Manual Testing**:
```bash
# 1. Create a profile in the app
# 2. Reset database:
docker compose exec postgres psql -U dating_user dating_db
DELETE FROM photos;
DELETE FROM profiles;
DELETE FROM users;
\q

# 3. Reload the app
# ✅ Expected: Onboarding screen appears (not success screen)
```

**Automated Testing**:
```bash
pytest tests/test_api.py::TestCheckProfileHandler -v
# ✅ 4/4 tests passing
```

---

## Issue #2: Grafana Panels Not Appearing

### Problem Description

Grafana dashboard was not displaying Loki datasource panels, showing "datasource loki was not found" error.

### Status

✅ **ALREADY FIXED IN REPOSITORY**

The issue was already resolved in the codebase. The `docker-compose.yml` correctly includes `loki` in Grafana's `depends_on` list:

```yaml
grafana:
  depends_on:
    - prometheus
    - loki  # ✅ Present
```

### Verification

To verify Grafana is working correctly:

```bash
# Start monitoring stack
docker compose --profile monitoring up -d

# Check Grafana logs
docker compose logs grafana | grep -i loki
# ✅ Should see: "Initializing Loki datasource"

# Open Grafana
open http://localhost:3000
# Login: admin/admin
# Navigate to: Configuration → Data Sources → Loki
# ✅ Status should show green checkmark "Data source is working"
```

**No code changes required for this issue.**

---

## Issue #3: App Version Missing from Profile Form and Success Screen

### Problem Description

The app version (v1.2.0) was only displayed on the welcome/onboarding screen. It was missing from:
- Profile creation form page
- Success screen ("Анкета создана!")

### Solution Implemented

1. **Added Version Display to Profile Form**
   - Location: `webapp/index.html`
   - Added version footer after "Создать анкету" button
   - Element: `<p class="app-version">v<span id="appVersionTextForm">1.2.0</span></p>`

2. **Added Version Display to Success Screen**
   - Location: `webapp/index.html`
   - Added version footer after features list
   - Element: `<p class="app-version">v<span id="appVersionTextSuccess">1.2.0</span></p>`

3. **Created Helper Function**
   - Location: `webapp/js/app.js`
   - Function: `updateVersionText()`
   - Purpose: Consistently update version on all pages

### Technical Details

**HTML Changes**:
```html
<!-- Profile Form -->
<form id="profileForm">
  <!-- ... form fields ... -->
  <button type="submit" class="button button-primary">Создать анкету</button>
  
  <!-- ✅ Added version -->
  <p class="app-version">v<span id="appVersionTextForm">1.2.0</span></p>
</form>

<!-- Success Screen -->
<div id="success-screen" class="container hidden">
  <div class="info-card text-center">
    <h2>✅ Анкета создана!</h2>
    <!-- ... content ... -->
    
    <!-- ✅ Added version -->
    <p class="app-version">v<span id="appVersionTextSuccess">1.2.0</span></p>
  </div>
</div>
```

**JavaScript Helper**:
```javascript
/**
 * Update version text on all pages
 */
function updateVersionText() {
  const versionElements = [
    'appVersionText',        // Welcome screen
    'appVersionTextForm',    // Profile form
    'appVersionTextSuccess'  // Success screen
  ];
  
  versionElements.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = APP_VERSION; // Currently '1.2.0'
    }
  });
}
```

**Usage in Navigation Functions**:
```javascript
function showOnboarding() {
  // ... show/hide logic ...
  updateVersionText(); // ✅ Set version
}

function startProfileCreation() {
  // ... show/hide logic ...
  updateVersionText(); // ✅ Set version
}

function showSuccessScreen() {
  // ... show/hide logic ...
  updateVersionText(); // ✅ Set version
}
```

### Testing

**Manual Testing**:
1. Open the webapp
2. Navigate through all screens:
   - Welcome screen → Check version appears at bottom
   - Profile form → Check version appears at bottom
   - Success screen → Check version appears at bottom
3. ✅ Version should be visible on all three pages

---

## Summary of Changes

### Files Modified

1. **`bot/api.py`** (+60 lines)
   - Added `check_profile_handler()` function
   - Added `/api/profile/check` route
   - Returns profile existence status from database

2. **`webapp/js/app.js`** (+81 lines, -13 lines)
   - Enhanced `checkUserProfile()` with database verification
   - Added `updateVersionText()` helper function
   - Updated navigation functions to call `updateVersionText()`

3. **`webapp/index.html`** (+4 lines)
   - Added version display to profile form page
   - Added version display to success screen page

4. **`tests/test_api.py`** (+143 lines)
   - Added `TestCheckProfileHandler` test class
   - 4 new test cases for profile check endpoint

**Total Changes**: 275 insertions, 13 deletions

### Test Results

All 206 tests passing (202 existing + 4 new):

```bash
$ pytest tests/ -v
============================= 206 passed in 4.11s ==============================

New tests:
✅ test_check_profile_exists
✅ test_check_profile_not_exists  
✅ test_check_profile_missing_user_id
✅ test_check_profile_invalid_user_id
```

---

## Deployment

To deploy these fixes:

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Restart services**:
   ```bash
   # Restart bot (includes API server)
   docker compose restart bot
   
   # Restart webapp (no rebuild needed, static files)
   docker compose restart webapp
   ```

3. **Verify fixes**:
   - Clear browser localStorage
   - Open webapp
   - ✅ Should see onboarding screen (not success screen)
   - Check version appears on all pages

---

## Related Documentation

- `docs/BUG_FIXES_OCTOBER_2025.md` - Previous bug fixes
- `docs/PRACTICAL_IMPACT.md` - Testing guide for profile fixes
- `PROFILE_CREATION_FLOW.md` - Profile creation workflow
- `bot/api.py` - API endpoint implementations

---

## Commit

**Commit**: `50c83c3`  
**Branch**: `copilot/fix-4d4e89e4-5ff3-4079-84e4-f233c013637c`  
**Date**: October 2024  
**Author**: GitHub Copilot + erliona
