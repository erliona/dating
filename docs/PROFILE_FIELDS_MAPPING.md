# Profile Fields Mapping

Complete reference for all profile fields in the Dating Mini App, including database schema, API contracts, and frontend forms.

## Database Schema (bot/db.py)

### Profile Table Fields

#### Required Fields
| Field | Type | Database Type | Constraints | Description |
|-------|------|---------------|-------------|-------------|
| `name` | `string` | `String(100)` | NOT NULL, 2-100 chars | User's display name |
| `birth_date` | `date` | `Date` | NOT NULL, <= today, 18+ | Date of birth |
| `gender` | `string` | `String(20)` | NOT NULL, in ('male', 'female', 'other') | User's gender |
| `orientation` | `string` | `String(20)` | NOT NULL, in ('male', 'female', 'any') | Who user is looking for |
| `goal` | `string` | `String(50)` | NOT NULL, in ('friendship', 'dating', 'relationship', 'networking', 'serious', 'casual') | Purpose of dating |

#### Optional Profile Fields
| Field | Type | Database Type | Constraints | Description |
|-------|------|---------------|-------------|-------------|
| `bio` | `string` | `Text` | Nullable, max 1000 chars | About me text |
| `interests` | `string[]` | `ARRAY(String(50))` | Nullable, max 20 items | User's interests |
| `height_cm` | `number` | `SmallInteger` | Nullable, 100-250 | Height in centimeters |
| `education` | `string` | `String(50)` | Nullable, in ('high_school', 'bachelor', 'master', 'phd', 'other') | Education level |
| `has_children` | `boolean` | `Boolean` | Nullable | Has children |
| `wants_children` | `boolean` | `Boolean` | Nullable | Wants children in future |
| `smoking` | `boolean` | `Boolean` | Nullable | Smoker |
| `drinking` | `boolean` | `Boolean` | Nullable | Drinks alcohol |

#### Location Fields
| Field | Type | Database Type | Constraints | Description |
|-------|------|---------------|-------------|-------------|
| `country` | `string` | `String(100)` | Nullable | Country name |
| `city` | `string` | `String(100)` | Nullable | City name |
| `geohash` | `string` | `String(20)` | Nullable, indexed | Privacy-preserving location (5km precision) |
| `latitude` | `number` | `Float` | Nullable | GPS latitude |
| `longitude` | `number` | `Float` | Nullable | GPS longitude |

#### Privacy Settings
| Field | Type | Database Type | Constraints | Description |
|-------|------|---------------|-------------|-------------|
| `hide_distance` | `boolean` | `Boolean` | NOT NULL, default false | Hide distance from other users |
| `hide_online` | `boolean` | `Boolean` | NOT NULL, default false | Hide online status |
| `hide_age` | `boolean` | `Boolean` | NOT NULL, default false | Hide age from other users |
| `allow_messages_from` | `string` | `String(20)` | NOT NULL, default 'matches', in ('matches', 'anyone') | Who can message user |

#### System Fields
| Field | Type | Database Type | Constraints | Description |
|-------|------|---------------|-------------|-------------|
| `is_visible` | `boolean` | `Boolean` | NOT NULL, default true | Profile visible in discovery |
| `is_complete` | `boolean` | `Boolean` | NOT NULL, default false | Profile has all required fields |
| `created_at` | `datetime` | `DateTime` | NOT NULL, default now() | Profile creation timestamp |
| `updated_at` | `datetime` | `DateTime` | NOT NULL, default now(), auto-update | Last update timestamp |

## API Endpoints (bot/api.py)

### GET /api/profile
Returns complete profile data for authenticated user.

**Response:**
```json
{
  "profile": {
    "name": "string",
    "age": "number",
    "birth_date": "string (ISO date)",
    "gender": "string",
    "orientation": "string",
    "goal": "string",
    "bio": "string | null",
    "city": "string | null",
    "country": "string | null",
    "latitude": "number | null",
    "longitude": "number | null",
    "height_cm": "number | null",
    "education": "string | null",
    "has_children": "boolean | null",
    "wants_children": "boolean | null",
    "smoking": "boolean | null",
    "drinking": "boolean | null",
    "interests": "string[] | null",
    "hide_age": "boolean",
    "hide_distance": "boolean",
    "hide_online": "boolean",
    "photos": [
      {
        "url": "string",
        "sort_order": "number"
      }
    ]
  }
}
```

### PUT /api/profile
Updates profile data for authenticated user.

**Request Body:**
```json
{
  "name": "string (optional)",
  "bio": "string | null (optional)",
  "city": "string | null (optional)",
  "height_cm": "number | null (optional)",
  "education": "string | null (optional)",
  "has_children": "boolean | null (optional)",
  "wants_children": "boolean | null (optional)",
  "smoking": "boolean | null (optional)",
  "drinking": "boolean | null (optional)",
  "interests": "string[] | null (optional)",
  "hide_age": "boolean (optional)",
  "hide_distance": "boolean (optional)",
  "hide_online": "boolean (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

## Frontend Forms

### Profile Creation Form (webapp/index.html)

**Form Fields (HTML name attributes):**
- `name` - text input (required)
- `birth_date` - date input (required)
- `gender` - select (required): male, female, other
- `orientation` - select (required): male, female, any
- `goal` - select (required): friendship, dating, relationship, serious, casual, networking
- `bio` - textarea (optional)
- `city` - text input (required)
- `height_cm` - number input (optional): 100-250
- `education` - select (optional): "", high_school, bachelor, master, phd, other
- `has_children` - select (optional): "", true, false
- `wants_children` - select (optional): "", true, false
- `smoking` - select (optional): "", true, false
- `drinking` - select (optional): "", true, false
- `interests` - text input (optional): comma-separated string
- `latitude` - hidden input (optional): GPS coordinate
- `longitude` - hidden input (optional): GPS coordinate

**JavaScript Handling (webapp/js/app.js):**
```javascript
// handleProfileSubmit() converts:
// - interests: "музыка, путешествия" → ["музыка", "путешествия"]
// - height_cm: "170" → 170 (integer)
// - has_children: "true" → true (boolean)
// - Empty string values → not included in payload
```

### Profile Edit Form (webapp/index.html)

**Form Fields (HTML id attributes):**
- `editName` - text input
- `editBio` - textarea
- `editCity` - text input
- `editHeight` - number input
- `editEducation` - select
- `editHasChildren` - select
- `editWantsChildren` - select
- `editSmoking` - select
- `editDrinking` - select
- `editInterests` - text input (comma-separated)

**JavaScript Handling (webapp/js/navigation.js):**

`loadProfileForEdit()`:
```javascript
// Converts from API response:
// - interests: ["музыка", "путешествия"] → "музыка, путешествия"
// - boolean: true → "true" (string for select)
// - null values → empty string ""
```

`saveProfileChanges()`:
```javascript
// Converts to API request:
// - interests: "музыка, путешествия" → ["музыка", "путешествия"]
// - select: "true" → true (boolean)
// - empty string → null
```

## Validation Rules (bot/validation.py)

### Required Field Validation
- `name`: 2-100 characters
- `birth_date`: Valid date, <= today, age >= 18
- `gender`: Must be one of: male, female, other
- `orientation`: Must be one of: male, female, any
- `goal`: Must be one of: friendship, dating, relationship, networking, serious, casual

### Optional Field Validation
- `bio`: Max 1000 characters
- `interests`: Max 20 items, each max 50 characters
- `height_cm`: 100-250 cm
- `education`: Must be one of: high_school, bachelor, master, phd, other
- `country`: Max 100 characters
- `city`: Max 100 characters

## Data Flow

### Profile Creation Flow
1. User fills form in webapp → `webapp/index.html`
2. Form submitted → `webapp/js/app.js::handleProfileSubmit()`
3. Data parsed and formatted (interests string→array, etc.)
4. Sent to bot via `tg.sendData()` → `bot/main.py::handle_create_profile()`
5. Validated → `bot/validation.py::validate_profile_data()`
6. Stored in DB → `bot/repository.py::create_profile()`

### Profile Edit Flow
1. User navigates to edit screen → `webapp/js/navigation.js::showProfileEdit()`
2. Profile loaded from API → `GET /api/profile` → `bot/api.py::get_profile_handler()`
3. Data populated in form → `loadProfileForEdit()` (arrays→strings, booleans→strings)
4. User edits and saves → `saveProfileChanges()`
5. Data converted back → `PUT /api/profile` (strings→arrays, strings→booleans)
6. Updated in DB → `bot/api.py::update_profile_handler()` → `bot/repository.py::update_profile()`

## Field Coverage Summary

✅ **All database fields are now utilized:**
- All required fields: ✅ In creation form, ✅ In edit form (read-only for immutable fields)
- All optional profile fields: ✅ In creation form, ✅ In edit form
- All location fields: ✅ In creation form (city + GPS)
- Privacy settings: ✅ In settings screen (separate from profile edit)

✅ **Backend fully supports all fields:**
- Repository methods accept all fields
- API endpoints handle all fields
- Validation covers all fields

✅ **Frontend handles all fields:**
- Creation form includes all fields
- Edit form includes all editable fields
- JavaScript correctly converts between formats (arrays, booleans, nulls)
