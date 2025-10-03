# Profile Check Fix - Flow Diagram

## Issue #1: Profile Check Logic Fix

### Problem: User sees onboarding screen even when profile exists in database

The screenshot showed this issue - user created a profile, reloaded the app, and saw "Начать знакомства" (Start Dating) button instead of the success screen.

---

## Before Fix ❌

```
User opens miniapp
    ↓
checkUserProfile() called
    ↓
Check localStorage.profile_created
    ↓
  ┌─────────────────────────────────┐
  │ Is localStorage set?            │
  └─────────┬────────────┬──────────┘
            │            │
         NO │            │ YES
            ↓            ↓
      Return FALSE   Check Backend API
            ↓            ↓
      Show Onboarding  Verify in DB
            ↓            ↓
         ❌ BUG!    Return result
```

**Problem**: If localStorage was empty/cleared, function returned `false` immediately WITHOUT checking the backend database!

This caused issues when:
- User cleared browser cache
- User switched devices
- localStorage was corrupted
- Testing with different accounts

---

## After Fix ✅

```
User opens miniapp
    ↓
checkUserProfile() called
    ↓
Check localStorage (for user ID validation)
    ↓
Clear if user ID mismatch
    ↓
ALWAYS check Backend API
    ↓
  ┌───────────────────────────────────┐
  │ Query Database:                   │
  │ GET /api/profile/check?user_id=X  │
  └────────────┬──────────────────────┘
               ↓
    ┌──────────────────────┐
    │ Database Check       │
    └────┬──────────────┬──┘
         │              │
    EXISTS │          │ NOT EXISTS
         ↓              ↓
    ┌────────────┐  ┌──────────────┐
    │ Profile    │  │ No Profile   │
    │ Found in   │  │ in Database  │
    │ Database   │  │              │
    └──────┬─────┘  └──────┬───────┘
           │                │
           ↓                ↓
    Sync localStorage  Clear localStorage
    - Set profile_created  - Remove profile_created
    - Set user_id          - Remove profile_data
           │                - Remove user_id
           │                │
           ↓                ↓
    Return TRUE      Return FALSE
           ↓                ↓
    Show Success     Show Onboarding
    Screen ✅        Screen ✅
```

**Solution**: Database is ALWAYS queried as the source of truth. LocalStorage is synced with database state.

---

## Code Comparison

### Old Code (Buggy) ❌

```javascript
async function checkUserProfile() {
  const profileCreated = localStorage.getItem('profile_created') === 'true';
  
  // If localStorage says no profile, definitely no profile
  if (!profileCreated) {
    return false;  // ❌ Returns without checking backend!
  }
  
  // Only checks backend if localStorage says profile exists
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/check?user_id=${currentUserId}`);
    const data = await response.json();
    return data.has_profile;
  } catch (error) {
    return profileCreated;
  }
}
```

**Problem**: Line `return false;` skips backend check entirely when localStorage is empty!

---

### New Code (Fixed) ✅

```javascript
async function checkUserProfile() {
  const currentUserId = tg?.initDataUnsafe?.user?.id;
  
  if (!currentUserId) {
    return false;
  }
  
  const profileCreated = localStorage.getItem('profile_created') === 'true';
  const storedUserId = localStorage.getItem('profile_user_id');
  
  // Clear old data if user ID mismatch
  if (profileCreated && storedUserId && storedUserId !== String(currentUserId)) {
    localStorage.removeItem('profile_created');
    localStorage.removeItem('profile_data');
    localStorage.removeItem('profile_user_id');
  }
  
  // ALWAYS verify with backend API (source of truth)
  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/check?user_id=${currentUserId}`);
    
    if (!response.ok) {
      return profileCreated; // Fallback only on error
    }
    
    const data = await response.json();
    const hasProfileInDB = data.has_profile;
    
    // Sync localStorage with database state
    if (hasProfileInDB && !profileCreated) {
      // Profile exists in DB but not in localStorage - update it
      localStorage.setItem('profile_created', 'true');
      localStorage.setItem('profile_user_id', String(currentUserId));
    } else if (!hasProfileInDB && profileCreated) {
      // Profile doesn't exist in DB but localStorage says it does - clear it
      localStorage.removeItem('profile_created');
      localStorage.removeItem('profile_data');
      localStorage.removeItem('profile_user_id');
    }
    
    return hasProfileInDB; // ✅ Always returns database state
  } catch (error) {
    return profileCreated; // Fallback only on error
  }
}
```

**Solution**: 
1. ✅ ALWAYS queries backend API
2. ✅ Database is source of truth
3. ✅ LocalStorage is synced automatically
4. ✅ Only falls back to localStorage on network errors

---

## Testing Scenarios

### Scenario 1: Normal Flow ✅
```
1. User creates profile → Saved to database
2. User closes miniapp → localStorage persists
3. User reopens miniapp → Backend confirms profile exists
4. Result: Shows success screen ✅
```

### Scenario 2: Cache Cleared ✅ (This was broken before!)
```
1. User creates profile → Saved to database
2. User clears cache → localStorage deleted
3. User reopens miniapp → Backend confirms profile exists
4. localStorage synced automatically → profile_created set to true
5. Result: Shows success screen ✅
```

### Scenario 3: Device Switch ✅
```
1. User creates profile on Phone A → Saved to database
2. User opens miniapp on Phone B → localStorage empty
3. Backend confirms profile exists
4. localStorage on Phone B synced
5. Result: Shows success screen ✅
```

### Scenario 4: Database Reset (Dev Testing) ✅
```
1. User creates profile → Saved to database
2. Developer resets database → Profile deleted from DB
3. User reopens miniapp → Backend says no profile
4. localStorage cleared automatically
5. Result: Shows onboarding screen ✅
```

---

## API Endpoint

The backend API endpoint that serves as source of truth:

**Endpoint**: `GET /api/profile/check?user_id={telegram_user_id}`

**Location**: `bot/api.py` - `check_profile_handler()`

**Response**:
```json
{
  "has_profile": true,
  "user_id": 123456789
}
```

**Logic**:
1. Queries PostgreSQL database
2. Looks up user by Telegram ID
3. Checks if profile exists for that user
4. Returns boolean result

**Tests**: `tests/test_api.py::TestCheckProfileHandler`
- ✅ `test_check_profile_exists` - Profile found
- ✅ `test_check_profile_not_exists` - Profile not found  
- ✅ `test_check_profile_missing_user_id` - Error handling
- ✅ `test_check_profile_invalid_user_id` - Validation

All tests passing! ✅

---

## Impact

**Before Fix**:
- ❌ User sees onboarding screen after cache clear
- ❌ Profile check unreliable across devices
- ❌ Developer testing confusing (database resets not reflected)

**After Fix**:
- ✅ Database is authoritative source of truth
- ✅ Works correctly across device switches
- ✅ Works correctly after cache clears
- ✅ LocalStorage automatically synced
- ✅ Developer testing consistent

---

## References

- Issue: баги (Issue #1)
- Documentation: `docs/BUG_FIXES_PROFILE_CHECK_GRAFANA.md`
- Code: `webapp/js/app.js` - `checkUserProfile()`
- API: `bot/api.py` - `check_profile_handler()`
- Tests: `tests/test_api.py::TestCheckProfileHandler`
