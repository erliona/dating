# Authentication & Session Handling

This document describes the authentication system implemented in the Next.js webapp.

## Overview

The webapp uses a secure authentication flow with Telegram Login and JWT tokens stored in httpOnly cookies. All authentication is handled server-side to prevent token exposure to client JavaScript.

## Architecture

### Flow Diagram

```
User (Telegram) → Login Page → /api/auth/tg → API Gateway → Auth Service
                                      ↓
                              Set httpOnly Cookies
                                      ↓
                              Redirect to App
```

### Components

1. **Login Page** (`/[locale]/login`)
   - Displays Telegram Login Widget
   - Handles authentication callback
   - Redirects to requested page after login

2. **Auth API Routes** (`/api/auth/*`)
   - `/api/auth/tg` - Exchange Telegram initData for JWT
   - `/api/auth/logout` - Clear authentication cookies
   - `/api/auth/refresh` - Refresh access token

3. **API Proxy** (`/api/proxy/*`)
   - Forwards requests to API Gateway
   - Extracts token from cookies and adds to Authorization header
   - Handles cookie forwarding

4. **Middleware** (`src/middleware.ts`)
   - Protects routes requiring authentication
   - Redirects unauthenticated users to login
   - Preserves i18n routing

5. **Auth Utilities** (`src/shared/lib/auth.ts`)
   - `logout()` - Log out user
   - `checkAuth()` - Check authentication status
   - `redirectToLogin()` - Redirect to login page
   - `handleAuthError()` - Handle 401/403 errors
   - `refreshToken()` - Refresh access token
   - `startTokenRefresh()` - Auto-refresh token before expiration

6. **React Hook** (`src/shared/hooks/use-auth.ts`)
   - `useAuth()` - Hook for client components
   - Provides logout and requireAuth functions

## Security Features

### Cookie Configuration

All authentication tokens are stored in httpOnly cookies with the following security settings:

```typescript
// Access Token (short-lived)
{
  httpOnly: true,              // Not accessible via JavaScript
  secure: true,                // Only sent over HTTPS (production)
  sameSite: "lax",             // CSRF protection while allowing Telegram widget redirects
  maxAge: 60 * 60,            // 1 hour (recommended: 15-60 minutes)
  path: "/",                   // Available to all routes
}

// Refresh Token (long-lived)
{
  httpOnly: true,
  secure: true,
  sameSite: "lax",
  maxAge: 7 * 24 * 60 * 60,   // 7 days (recommended: 7-30 days)
  path: "/",
}
```

### Content Security Policy (CSP)

The CSP headers are environment-specific:

**Production (Strict):**

- `script-src`: `'self' https://telegram.org https://oauth.telegram.org` (NO unsafe directives)
- `frame-src`: `https://oauth.telegram.org https://telegram.org https://*.telegram.org https://t.me`
- `frame-ancestors`: `'self'` (allows same-origin framing)
- `connect-src`: Restricted to API Gateway domain and WSS (per-environment)

**Development (Relaxed):**

- `script-src`: Includes `'unsafe-eval'` and `'unsafe-inline'` for Next.js hot reload
- `connect-src`: Allows all localhost ports and API Gateway

### CSRF Protection

State-changing requests (POST, PUT, DELETE, PATCH) through `/api/proxy/*` are protected by:

- **Origin/Referer validation**: Verifies requests come from same origin
- **SameSite cookies**: `lax` setting prevents CSRF in most scenarios
- Server-side validation before proxying to backend

### Open Redirect Protection

Login redirect URLs are validated to prevent open redirect attacks:

- **Relative paths only**: Only URLs starting with `/` are allowed
- **Protocol validation**: URLs with `//` prefix (protocol-relative) are rejected
- **Default fallback**: Invalid URLs default to `/` (home page)
- Applied in both login page and middleware

### Token Management

- **Access Token**: 1-hour expiration, used for API requests (shorter TTL for better security)
- **Refresh Token**: 7-day expiration, used to renew access token
- **Auto-Refresh**: Token refreshed every 50 minutes (10 minutes before expiration)
- **⚠️ CRITICAL**: Currently both tokens use the same JWT value. Backend MUST generate separate refresh tokens with:
  - Different signature/secret
  - Longer TTL (7-30 days)
  - Token rotation on use
  - Different audience/scope

## Usage

### Protected Routes

Add routes to the `PROTECTED_ROUTES` array in `src/middleware.ts`:

```typescript
const PROTECTED_ROUTES = ["/profile", "/matches", "/chat"];
```

### Client-Side Auth Check

```typescript
import { useAuth } from "@/shared/hooks/use-auth";

function MyComponent() {
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    // User will be redirected to /login
  };

  return <button onClick={handleLogout}>Logout</button>;
}
```

### API Requests

All requests through `/api/proxy/*` automatically include authentication:

```typescript
// Automatically includes auth token from cookie
const response = await fetch("/api/proxy/profiles/123", {
  credentials: "include", // Required
});

if (response.status === 401) {
  // Token expired or invalid - middleware will redirect
}
```

### Handling Auth Errors

```typescript
import { handleAuthError } from "@/shared/lib/auth";

try {
  const response = await fetch("/api/proxy/profiles/123", {
    credentials: "include",
  });

  if (!response.ok) {
    // Automatically redirects on 401/403
    if (handleAuthError(response.status)) {
      return;
    }
    throw new Error("Request failed");
  }

  const data = await response.json();
} catch (error) {
  console.error(error);
}
```

## Testing

### E2E Tests

Auth tests are located in `tests/e2e/auth.spec.ts`:

```bash
npm test tests/e2e/auth.spec.ts
```

### Manual Testing

1. **Login Flow**:
   - Navigate to `/en/login`
   - Widget should load from Telegram
   - After successful login, should redirect to home

2. **Protected Routes**:
   - Try accessing `/en/profile` without auth
   - Should redirect to `/en/login?reason=unauthorized`

3. **Logout**:
   - Click logout button
   - Cookies should be cleared
   - Should redirect to login page

4. **Token Refresh**:
   - After 23 hours, token should auto-refresh
   - Check browser console for refresh errors

## Environment Variables

Required variables for authentication:

```bash
# Backend API Gateway URL
API_URL=http://api-gateway:8080

# Telegram Bot Token (for initData validation)
BOT_TOKEN=your_bot_token_here

# JWT Secret (must match backend)
JWT_SECRET=your_jwt_secret_here
```

## Troubleshooting

### Login Widget Not Loading

**Issue**: Telegram widget doesn't appear on login page

**Solution**:

1. Check CSP headers allow `https://telegram.org`
2. Verify `data-telegram-login` attribute has correct bot username
3. Check browser console for CSP violations

### 401 Unauthorized Errors

**Issue**: API requests return 401 even after login

**Solution**:

1. Check cookies are set (DevTools → Application → Cookies)
2. Verify `credentials: "include"` in fetch requests
3. Check API proxy forwards cookies correctly
4. Verify backend JWT secret matches

### Infinite Redirect Loop

**Issue**: Redirecting between login and protected pages

**Solution**:

1. Check middleware protected routes configuration
2. Verify login page is in `PUBLIC_ROUTES`
3. Check cookie domain and path settings

### Token Not Refreshing

**Issue**: Auto-refresh not working

**Solution**:

1. Check `startTokenRefresh()` is called on app load
2. Verify refresh token exists in cookies
3. Check backend `/api/auth/refresh` endpoint

## API Reference

### POST /api/auth/tg

Exchange Telegram initData for JWT tokens.

**Request:**

```json
{
  "initData": "user=...&hash=..."
}
```

**Response:**

```json
{
  "success": true,
  "user_id": 123456,
  "username": "johndoe"
}
```

**Sets Cookies:**

- `access_token` (httpOnly, 24h)
- `refresh_token` (httpOnly, 7d)

### POST /api/auth/logout

Clear authentication cookies.

**Response:**

```json
{
  "success": true
}
```

### POST /api/auth/refresh

Refresh access token using refresh token.

**Response:**

```json
{
  "success": true,
  "user_id": 123456
}
```

**Updates Cookies:**

- `access_token` (httpOnly, 24h)

## Future Improvements

- [ ] **Priority**: Implement separate refresh token generation on backend (currently uses same token)
- [ ] Add session management (track active sessions)
- [ ] Implement "remember me" functionality
- [ ] Add 2FA support
- [ ] Implement rate limiting on auth endpoints
- [ ] Add login activity logging
- [ ] Support multiple device sessions
- [ ] Add "logout all devices" functionality
- [ ] Consider nonce-based CSP for scripts in production (if Next.js auto-nonce is insufficient)

## Related Documentation

- [Security Configuration](./SECURITY.md)
- [API Gateway Routes](../docs/API_GATEWAY_ROUTES.md)
- [Next.js Authentication Patterns](https://nextjs.org/docs/app/building-your-application/authentication)
