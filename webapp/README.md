# Dating Mini App (WebApp)

Modern Telegram Mini Application for the Dating Bot, following industry best practices and standards.

## 🎯 Overview

This is a completely rebuilt mini-app designed with modern web standards and dating app industry best practices (inspired by Tinder, Bumble, etc.).

### Key Features

- ✅ **Card-based swipe interface** - Industry standard for dating apps
- ✅ **Profile creation & editing** - Simple, intuitive form
- ✅ **Discover mode** - Swipe through potential matches
- ✅ **Matches list** - View all your mutual likes
- ✅ **Offline support** - Queue interactions when offline
- ✅ **Haptic feedback** - Enhanced mobile experience
- ✅ **Theme support** - Follows Telegram light/dark theme
- ✅ **Responsive design** - Works on all screen sizes
- ✅ **Accessibility** - ARIA labels, keyboard navigation

## 🏗️ Architecture

### Design Principles

1. **Separation of Concerns**: Clean separation between UI, business logic, and data layer
2. **Mobile-First**: Optimized for mobile devices
3. **Progressive Enhancement**: Works even without JavaScript (basic functionality)
4. **Performance**: Minimal bundle size, no external dependencies
5. **Accessibility**: WCAG 2.1 AA compliant

### File Structure

```
webapp/
├── index.html          # Main HTML structure (clean, semantic)
├── css/
│   └── style.css      # Modern CSS with CSS variables for theming
└── js/
    └── app.js         # Modular JavaScript with clear separation
```

### Code Architecture

**app.js** is organized into logical modules:

- **Telegram WebApp Integration**: Initialization, theme handling
- **State Management**: Centralized app state
- **API Service Layer**: All backend communication
- **UI Controller**: Display logic separation
- **Event Handlers**: User interaction handling
- **Validation**: Client-side form validation

## 🎨 UI/UX Design

### Screens

1. **Loading**: Initial load state
2. **Profile Form**: Create/edit user profile
3. **Discover**: Card-based swipe interface
4. **Matches**: List of mutual likes
5. **Error**: Error state with retry option

### Navigation

Bottom navigation bar with 3 tabs:
- 👤 Profile
- 🔍 Discover (default)
- 💕 Matches

### Interactions

**Card Swiping**:
- Swipe right → Like (with haptic feedback)
- Swipe left → Dislike (with haptic feedback)
- Tap ❤️ button → Like
- Tap 👎 button → Dislike

## 📡 Data Flow

### Profile Creation

```
User fills form → Client validation → sendData to Bot → Bot processes → DB save
```

### Interactions (Like/Dislike)

```
User swipes → Queue locally → Include in next profile update → Bot processes → DB save
```

**Why queue?** Telegram's `sendData()` closes the WebApp. Queuing allows users to swipe multiple profiles before the app closes.

### Data Persistence

- **Profile data**: Sent to bot via `tg.sendData()`
- **Interactions queue**: Stored in localStorage, sent with profile updates
- **Theme preference**: Follows Telegram app theme automatically

## 🔧 Integration with Backend

### Payload Format

**Profile Creation**:
```json
{
  "action": "create_profile",
  "name": "John",
  "age": 25,
  "gender": "male",
  "preference": "female",
  "bio": "Hello world",
  "location": "Moscow",
  "interests": ["Music", "Travel"],
  "goal": "serious",
  "photo_url": "https://example.com/photo.jpg",
  "queued_interactions": [
    {
      "target_user_id": 123,
      "action": "like",
      "timestamp": 1234567890
    }
  ]
}
```

**Profile Deletion**:
```json
{
  "action": "delete"
}
```

### Bot Handler

The bot's `webapp_handler` function (in `bot/main.py`) processes these payloads:
- Validates required fields
- Sanitizes user input
- Creates/updates profile in database
- Processes queued interactions
- Sends confirmation message to user

## 🧪 Testing

### Backend Integration Tests

All backend integration is tested in `tests/test_webapp_handler.py`:
- ✅ Profile creation with valid data
- ✅ Missing/invalid data handling
- ✅ Profile deletion
- ✅ Queued interactions processing
- ✅ Error handling

Run tests:
```bash
pytest tests/test_webapp_handler.py -v
```

### Manual Testing Checklist

- [ ] Profile form validation
- [ ] Profile submission reaches bot
- [ ] Data appears in database
- [ ] Card swiping works smoothly
- [ ] Haptic feedback on interactions
- [ ] Theme switches with Telegram theme
- [ ] Works on mobile devices
- [ ] Works on desktop browsers
- [ ] Offline queue functionality
- [ ] Error states display correctly

## 🚀 Deployment

The webapp is served by nginx in the Docker stack. No build step required - it's pure HTML/CSS/JS.

### Development

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# WebApp available at: http://localhost:8080
```

### Production

```bash
# Start production environment
docker compose up -d

# WebApp available at: https://your-domain.com
```

## 🎓 Best Practices Implemented

### Industry Standards

1. **Card-Based UI**: Standard for dating apps (Tinder, Bumble, Hinge)
2. **Swipe Gestures**: Touch-optimized for mobile
3. **Minimal Profile Form**: Only essential fields
4. **Visual Hierarchy**: Clear, scannable content
5. **Instant Feedback**: Haptic and visual feedback

### Web Standards

1. **Semantic HTML**: Proper HTML5 elements
2. **CSS Variables**: Easy theming
3. **No Build Tools**: Pure web technologies
4. **Progressive Enhancement**: Works without JS
5. **Accessibility**: ARIA labels, focus states
6. **Mobile-First**: Responsive design
7. **Performance**: Lazy loading, minimal JS

### Telegram Mini App Standards

1. **WebApp SDK Integration**: Proper initialization
2. **Theme Compatibility**: Follows system theme
3. **Safe Area Handling**: viewport-fit=cover
4. **Haptic Feedback**: Native-like experience
5. **Closing Confirmation**: Prevents accidental exits

## 📝 Migration from Old WebApp

### What Changed

**Removed**:
- ❌ Complex onboarding flow (4 steps)
- ❌ Multiple navigation pages
- ❌ Test profiles section
- ❌ Settings page (simplified)
- ❌ 2700+ lines of code

**Added**:
- ✅ Card-based swipe interface
- ✅ Cleaner, more maintainable code (< 600 lines)
- ✅ Better mobile experience
- ✅ Modern architecture
- ✅ Improved performance

**Kept**:
- ✅ All essential functionality
- ✅ Profile creation/editing
- ✅ Backend integration
- ✅ Offline queuing
- ✅ Theme support

### Breaking Changes

**None!** The payload format remains compatible with the existing bot handler.

## 🔮 Future Enhancements

Potential improvements (not in scope of current implementation):

1. **Photo Upload**: Direct photo upload (not just URLs)
2. **Filters**: Age range, distance filters
3. **Super Like**: Special interaction type
4. **Undo**: Undo last swipe
5. **Profile Preview**: Preview your own profile
6. **Animations**: Enhanced card animations
7. **PWA**: Install as standalone app

## 📚 References

- [Telegram Mini Apps Documentation](https://core.telegram.org/bots/webapps)
- [WebApp SDK Reference](https://core.telegram.org/bots/webapps#initializing-mini-apps)
- [Mobile UX Best Practices](https://developers.google.com/web/fundamentals/design-and-ux/principles)
- [Dating App UX Patterns](https://uxdesign.cc/tinder-ux-design-teardown-part-1-of-2-user-onboarding-68a05aa3478c)

## 🤝 Contributing

When making changes to the webapp:

1. Keep code modular and well-commented
2. Follow the existing architecture
3. Test on mobile devices
4. Maintain backward compatibility with bot handler
5. Update this README with significant changes

## 📄 License

Part of the Dating Bot project. See main repository LICENSE.
