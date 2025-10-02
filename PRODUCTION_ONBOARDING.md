# Production Onboarding Flow Implementation

## Overview

This document describes the production onboarding flow implementation for the Dating Mini App. The implementation ensures new users go through a guided onboarding process before creating their profile.

## User Flow

### For New Users
1. User starts bot with `/start` command
2. Bot sends welcome message with "🚀 Открыть Mini App" button
3. User clicks button and Mini App opens
4. Mini App detects user is new (no profile in localStorage)
5. **Onboarding Flow (5 steps)**:
   - **Step 1**: Welcome screen with app features
   - **Step 2**: Preview of basic information needed
   - **Step 3**: Optional photo upload
   - **Step 4**: Preview of additional profile details
   - **Step 5**: Ready to create profile
6. After completing onboarding, user fills out profile form
7. Profile is validated and saved (currently in localStorage)
8. Success screen is shown with placeholder content

### For Returning Users
1. User opens Mini App
2. Mini App detects existing profile
3. Success screen is shown immediately (skip onboarding)

## Implementation Details

### Bot Changes (`bot/main.py`)
- Added `/start` command handler
- Handler shows keyboard with WebApp button
- Message in Russian: "Добро пожаловать в Dating Mini App!"

### WebApp Changes

#### HTML (`webapp/index.html`)
- **Onboarding Section**: 5 steps with progressive disclosure
- **Profile Form**: Complete form with validation
- **Success Screen**: Placeholder for future features

#### CSS (`webapp/css/style.css`)
- Onboarding card styles with animations
- Progress bar with gradient
- Photo upload zone with drag-and-drop styling
- Form field styles
- Responsive design for mobile

#### JavaScript (`webapp/js/app.js`)
Key functions:
- `hasCompletedOnboarding()`: Checks localStorage for onboarding status
- `checkUserProfile()`: Checks if user has created profile
- `showOnboarding()`: Displays onboarding flow
- `nextOnboardingStep()`: Advances to next step
- `startProfileCreation()`: Shows profile form
- `handleProfileSubmit()`: Validates and saves profile
- `showSuccessScreen()`: Shows placeholder after success

## User State Management

Currently using localStorage for state persistence:
- `onboarding_completed`: Boolean flag for onboarding status
- `profile_created`: Boolean flag for profile existence
- `profile_data`: JSON string with profile data

### Future Enhancement
In production, these should be replaced with:
1. Backend API calls to check user profile
2. Database storage for profile data
3. JWT token authentication
4. Session management

## Validation

### Age Verification (18+)
- Client-side validation in JavaScript
- Calculates age from birth_date
- Shows error if under 18

### Required Fields
- Name (2-100 characters)
- Birth date
- Gender (male/female/other)
- Orientation (male/female/any)
- Goal (friendship/dating/relationship/serious/casual/networking)

### Optional Fields
- Bio (up to 1000 characters)
- City
- Photo

## Testing

### Manual Testing Steps
1. Open bot and send `/start`
2. Click "🚀 Открыть Mini App" button
3. Verify onboarding appears (5 steps)
4. Navigate through all steps
5. Fill profile form with valid data
6. Submit and verify success screen
7. Close and reopen Mini App
8. Verify success screen shows immediately (no onboarding)

### Edge Cases
- User under 18: Shows error message
- Empty required fields: Browser validation prevents submit
- Large photo: JavaScript validates file size (5MB limit)

## Integration with Backend (TODO)

To connect to the backend profile API:

1. **Add API endpoint** in backend:
   ```python
   @router.post("/api/profile")
   async def create_profile(profile_data: ProfileData, user: User = Depends(get_current_user)):
       # Validate and save profile
       pass
   ```

2. **Update JavaScript** to call API:
   ```javascript
   async function handleProfileSubmit(form) {
       const response = await fetch('/api/profile', {
           method: 'POST',
           headers: {
               'Content-Type': 'application/json',
               'Authorization': `Bearer ${jwt_token}`
           },
           body: JSON.stringify(profileData)
       });
       // Handle response
   }
   ```

3. **Add authentication**:
   - Use Telegram initData for auth
   - Validate with backend
   - Get JWT token
   - Store token in memory

## Acceptance Criteria

✅ Bot sends `/start` message with Mini App button  
✅ New users see 5-step onboarding flow  
✅ Onboarding has progress indicators  
✅ Photo upload is optional  
✅ Profile form validates all fields  
✅ Age validation enforces 18+ requirement  
✅ Profile data is saved (localStorage for now)  
✅ Success screen shows after profile creation  
✅ Returning users skip onboarding  
✅ UI is responsive and mobile-friendly  
✅ Telegram theme support (light/dark)  
✅ Haptic feedback on interactions  

## Future Enhancements

1. **Backend Integration**: Replace localStorage with API calls
2. **Multiple Photos**: Support 1-3 photos as per Epic B
3. **Geolocation**: Request location permission
4. **Privacy Settings**: Hide distance/age/online status
5. **Edit Profile**: Allow users to update their profile
6. **Profile Preview**: Show profile before final submission
7. **Analytics**: Track onboarding completion rate
8. **A/B Testing**: Test different onboarding flows

## Files Changed

- `bot/main.py`: Added /start handler
- `webapp/index.html`: Added onboarding and form UI
- `webapp/css/style.css`: Added onboarding styles
- `webapp/js/app.js`: Added onboarding logic
- `examples/webapp_auth_handler.py`: Updated to match new flow
