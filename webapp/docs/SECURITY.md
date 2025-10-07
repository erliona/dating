# Security Configuration

## Content Security Policy (CSP)

The webapp implements strict CSP headers that adapt to the environment.

### Development Mode

In development (`NODE_ENV !== 'production'`), CSP allows:

- **connect-src**: All localhost connections including WebSocket
  - `'self'`
  - `http://localhost:*`
  - `https://localhost:*`
  - `http://api-gateway:*`
  - `ws://localhost:*`

### Production Mode

In production, CSP restricts connections to only the configured API Gateway:

- **connect-src**: Limited to API domain from `NEXT_PUBLIC_API_URL`
  - `'self'`
  - `https://${API_DOMAIN}`
  - `http://${API_DOMAIN}:*`
  - `wss://${API_DOMAIN}`

### Configuration

Set `NEXT_PUBLIC_API_URL` to control allowed API connections:

```env
# Development
NEXT_PUBLIC_API_URL=http://localhost:8080

# Docker Compose
NEXT_PUBLIC_API_URL=http://api-gateway:8080

# Production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Other CSP Directives

- **default-src**: `'self'` - Only same-origin by default
- **script-src**: `'self' 'unsafe-eval'` - Self + eval for Next.js dev mode
- **style-src**: `'self' 'unsafe-inline'` - Self + inline for Tailwind
- **img-src**: `'self' data: blob: https:` - Flexible image sources
- **font-src**: `'self' data:` - Self + data URLs for fonts
- **frame-ancestors**: `'none'` - No embedding (clickjacking protection)

## Security Headers

### X-Powered-By

**Disabled** - Prevents version disclosure

### X-Frame-Options

**Value**: `DENY` - Prevents clickjacking by blocking all framing

### X-Content-Type-Options

**Value**: `nosniff` - Prevents MIME type sniffing

### Referrer-Policy

**Value**: `strict-origin-when-cross-origin` - Sends origin only for cross-origin requests

### Permissions-Policy

**Value**: `camera=(), microphone=(), geolocation=()` - Blocks sensor access

## Modifying CSP for Custom Domains

To allow additional domains (fonts, CDN, analytics):

1. Edit `webapp/next.config.ts`
2. Add domains to appropriate directives:

```typescript
const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              // ... existing rules
              "font-src 'self' data: https://fonts.gstatic.com",
              "img-src 'self' data: blob: https: https://cdn.yourdomain.com",
              // ... more rules
            ].join("; "),
          },
        ],
      },
    ];
  },
};
```

## Testing CSP

1. Open browser DevTools (F12)
2. Check Console for CSP violations
3. Adjust directives as needed
4. Test in both development and production modes

## Recommended Tools

- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) - Validate your policy
- [Report URI](https://report-uri.com/) - Monitor CSP violations in production
