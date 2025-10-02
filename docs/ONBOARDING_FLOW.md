# Onboarding Flow Diagram

## User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER STARTS BOT                         │
│                         /start command                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BOT WELCOME MESSAGE                          │
│  "👋 Добро пожаловать в Dating Mini App!"                       │
│  [🚀 Открыть Mini App] ← WebApp Button                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼ User clicks button
┌─────────────────────────────────────────────────────────────────┐
│                    MINI APP OPENS                               │
│                 Telegram WebApp SDK loads                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CHECK USER STATE                               │
│  localStorage.getItem('profile_created')                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    ┌───────▼────────┐            ┌────────▼────────┐
    │  NEW USER      │            │ RETURNING USER  │
    │ (no profile)   │            │ (has profile)   │
    └───────┬────────┘            └────────┬────────┘
            │                               │
            ▼                               │
┌──────────────────────┐                   │
│  ONBOARDING STEP 1   │                   │
│  👋 Welcome          │                   │
│  • Features          │                   │
│  • Benefits          │                   │
│  [Progress: 0%]      │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│  ONBOARDING STEP 2   │                   │
│  📝 Basic Info       │                   │
│  • Name              │                   │
│  • Age               │                   │
│  • Gender            │                   │
│  [Progress: 25%]     │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│  ONBOARDING STEP 3   │                   │
│  📸 Photo Upload     │                   │
│  • Upload zone       │                   │
│  • Preview           │                   │
│  • Skip option       │                   │
│  [Progress: 50%]     │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│  ONBOARDING STEP 4   │                   │
│  ✨ Details          │                   │
│  • Interests         │                   │
│  • Location          │                   │
│  • Goals             │                   │
│  [Progress: 75%]     │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│  ONBOARDING STEP 5   │                   │
│  🎉 Ready            │                   │
│  • Checklist         │                   │
│  • Summary           │                   │
│  [Progress: 100%]    │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│   PROFILE FORM       │                   │
│  • Name              │                   │
│  • Birth date        │                   │
│  • Gender            │                   │
│  • Orientation       │                   │
│  • Goal              │                   │
│  • Bio (optional)    │                   │
│  • City (optional)   │                   │
│  [Submit]            │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼ Validate & Save               │
┌──────────────────────┐                   │
│   AGE VALIDATION     │                   │
│   Must be 18+        │                   │
└──────────┬───────────┘                   │
           │                               │
           ▼                               │
┌──────────────────────┐                   │
│  SAVE TO STORAGE     │                   │
│  localStorage        │                   │
│  (or API in prod)    │                   │
└──────────┬───────────┘                   │
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │    SUCCESS SCREEN        │
            │  ✅ Profile Created      │
            │  • Confirmation          │
            │  • Placeholder content   │
            │  • Next steps            │
            └──────────────────────────┘
```

## State Transitions

```
State: NEW_USER
├── onboarding_completed: false
└── profile_created: false

State: ONBOARDING_IN_PROGRESS
├── onboarding_completed: false
├── profile_created: false
└── currentStep: 1-5

State: ONBOARDING_COMPLETED
├── onboarding_completed: true
└── profile_created: false

State: PROFILE_CREATED
├── onboarding_completed: true
└── profile_created: true
```

## Screen Flow Details

### Onboarding Screens (5 steps)

**Step 1: Welcome**
- Emoji: 👋
- Title: "Добро пожаловать!"
- Features: 3 items with icons
- Button: "Начать"
- Progress: 0%

**Step 2: Basic Info Preview**
- Emoji: 📝
- Title: "Базовая информация"
- Preview: 4 items checklist
- Button: "Продолжить"
- Progress: 25%

**Step 3: Photo Upload**
- Emoji: 📸
- Title: "Добавьте фото"
- Upload zone: Click/drag-drop
- Preview: Shows uploaded image
- Buttons: "Пропустить" / "Далее"
- Progress: 50%

**Step 4: Details Preview**
- Emoji: ✨
- Title: "Дополнительно"
- Preview: 4 items checklist
- Button: "Продолжить"
- Progress: 75%

**Step 5: Ready**
- Emoji: 🎉
- Title: "Отлично!"
- Checklist: 3 items completed
- Button: "Создать анкету"
- Progress: 100%

### Profile Form

**Required Fields:**
1. Name (2-100 chars)
2. Birth date (18+)
3. Gender (male/female/other)
4. Orientation (male/female/any)
5. Goal (6 options)

**Optional Fields:**
1. Bio (up to 1000 chars)
2. City

**Validation:**
- Age check: Must be 18+
- Required field check: Browser HTML5 validation
- Length check: min/max attributes

### Success Screen

**Content:**
- Title: "✅ Анкета создана!"
- Message: Success confirmation
- Placeholder section:
  - "🚀 Скоро здесь появятся новые возможности:"
  - List of upcoming features:
    - Просмотр других анкет
    - Система совпадений
    - Обмен сообщениями

## Technical Implementation

### File Structure
```
dating/
├── bot/
│   └── main.py              (Updated: /start handler)
├── webapp/
│   ├── index.html           (Updated: Onboarding UI)
│   ├── css/
│   │   └── style.css        (Updated: Onboarding styles)
│   └── js/
│       └── app.js           (Updated: Onboarding logic)
└── examples/
    └── webapp_auth_handler.py (Updated: Match main.py)
```

### Key Functions

**JavaScript (webapp/js/app.js):**
```javascript
// State management
hasCompletedOnboarding()      // Check localStorage
checkUserProfile()             // Check if profile exists

// UI flow
showOnboarding()              // Display step 1
showOnboardingStep(step)      // Show specific step
nextOnboardingStep()          // Advance to next
startProfileCreation()        // Show form
handleProfileSubmit()         // Validate & save
showSuccessScreen()           // Final screen

// Photo upload
setupPhotoUpload()            // Initialize handlers
handlePhotoUpload(file)       // Process image

// Validation
validateAge()                 // 18+ check
validateForm()                // Required fields
```

### CSS Classes

**Onboarding:**
- `.onboarding-step` - Container for each step
- `.onboarding-card` - Centered card layout
- `.onboarding-title` - Main heading
- `.onboarding-subtitle` - Secondary text
- `.onboarding-features` - Feature list
- `.feature-item` - Individual feature
- `.onboarding-progress` - Progress section
- `.progress-bar` - Progress container
- `.progress-fill` - Animated fill

**Form:**
- `.form-group` - Form field container
- `.error-message` - Validation errors
- `.placeholder-content` - Success screen content

### Animations

1. **Fade In**: Cards appear with opacity and translation
2. **Progress Bar**: Width transitions smoothly
3. **Button Hover**: Opacity change
4. **Button Active**: Scale down effect
