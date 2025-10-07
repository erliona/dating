# Dating Web App - Next.js 15

Public web application for Dating service built with Next.js 15, TypeScript, Tailwind CSS, and shadcn/ui.

## 🚀 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui + lucide-react
- **State Management**: TanStack Query
- **Internationalization**: next-intl (ru/en)
- **Code Quality**: ESLint + Prettier

## 📁 Project Structure

```
webapp/
├── src/
│   ├── app/
│   │   ├── [locale]/         # Localized routes
│   │   │   ├── layout.tsx    # Locale-specific layout
│   │   │   └── page.tsx      # Home page
│   │   ├── layout.tsx        # Root layout
│   │   └── globals.css       # Global styles
│   ├── shared/
│   │   ├── lib/              # Utilities (cn, etc.)
│   │   ├── providers/        # React Query provider
│   │   └── ui/               # shadcn/ui components (to be added)
│   ├── entities/             # Domain entities (to be added)
│   ├── features/             # Feature components
│   │   └── language-switcher/  # Language switcher component
│   └── i18n/                 # i18n configuration
│       ├── routing.ts        # Route configuration
│       └── request.ts        # Server-side i18n config
├── messages/
│   ├── ru.json               # Russian translations
│   └── en.json               # English translations
├── public/                   # Static assets
├── Dockerfile                # Production Docker build
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.ts        # Tailwind configuration
└── package.json              # Dependencies and scripts
```

## 🛠️ Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

The app will automatically redirect to `/ru` (default locale) or `/en`.

### Available Scripts

```bash
# Development
npm run dev          # Start dev server (port 3000)

# Production
npm run build        # Build for production
npm start            # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run format       # Format code with Prettier
npm run format:check # Check formatting
npm run type-check   # Run TypeScript compiler
```

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t dating-webapp .
```

### Run with Docker Compose

```bash
# From the project root
docker compose --profile webapp up -d
```

The webapp will be available at:

- **Local**: http://localhost:3000
- **Traefik**: https://app.yourdomain.com (production)

### Environment Variables

Create `.env.local` for local development:

```env
# API Configuration (optional)
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 🔗 Monorepo Integration

### API Gateway Connection

The webapp communicates with the backend through a secure API proxy:

**Local Development:**

```bash
# Start API Gateway and services
docker compose up -d api-gateway profile-service

# Start webapp in dev mode
cd webapp
npm run dev
```

**Environment Variables:**

```env
# Backend API (Server-side)
NEXT_PUBLIC_API_URL=http://api-gateway:8080  # Docker Compose
# or
NEXT_PUBLIC_API_URL=http://localhost:8080     # Local development

# Public Site URL (for sitemap, etc.)
NEXT_PUBLIC_SITE_URL=https://app.your-domain.com

# Optional: Custom webapp port
WEBAPP_PORT=3000
```

**Required for Production:**

- `NEXT_PUBLIC_API_URL` - Backend API Gateway URL
- `NEXT_PUBLIC_SITE_URL` - Public site URL for SEO
- `BOT_TOKEN` - For Telegram integration (if using Mini App)

### Docker Compose Profiles

The webapp service is profile-gated:

```bash
# Start only backend services
docker compose up -d

# Start with webapp
docker compose --profile webapp up -d

# Start with monitoring + webapp
docker compose --profile monitoring --profile webapp up -d
```

### API Integration Example

```typescript
import { apiClient } from "@/shared/lib/api-client";

// All requests go through /api/proxy with httpOnly cookies
const profile = await apiClient.get("/profiles/123");
const newProfile = await apiClient.post("/profiles", { name: "John", age: 25 });
```

The API proxy (`/api/proxy/[...path]`) automatically:

- Forwards requests to API Gateway
- Handles httpOnly cookies (secure token storage)
- Manages CORS
- Returns proper error responses

## 🌍 Internationalization

The app supports Russian (default) and English.

### Adding New Languages

1. Add locale to `src/i18n/routing.ts`:

```typescript
locales: ["ru", "en", "es"], // Add new locale
```

2. Create translation file `messages/es.json`:

```json
{
  "home": {
    "title": "Bienvenido a Dating",
    "description": "Aplicación de citas en Telegram",
    "getStarted": "Comenzar"
  }
}
```

### Using Translations

```tsx
import { useTranslations } from "next-intl";

export function MyComponent() {
  const t = useTranslations("home");
  return <h1>{t("title")}</h1>;
}
```

## 🎨 Adding UI Components

This project is set up for shadcn/ui. To add components:

```bash
# Example: Add Button component
npx shadcn@latest add button

# Example: Add Card component
npx shadcn@latest add card
```

Components will be added to `src/shared/ui/`.

## 🔧 Configuration

### Path Aliases

The project uses `@/*` alias for imports:

```typescript
import { cn } from "@/shared/lib/utils";
import { QueryProvider } from "@/shared/providers/query-provider";
```

### ESLint & Prettier

- ESLint configured with Next.js rules
- Prettier configured with Tailwind plugin for class sorting
- Run `npm run format` before committing

### TypeScript

Strict mode enabled. Run `npm run type-check` to verify types.

## 🧪 Testing

### Smoke Tests (Playwright)

```bash
# Run all tests
npm test

# Run with UI
npm run test:ui

# Run in headed mode
npm run test:headed
```

**Tests include:**

- Health endpoint verification
- Homepage rendering
- Language switching
- API proxy accessibility

### Health Check

The webapp exposes a health endpoint for monitoring:

```bash
curl http://localhost:3000/api/health
```

Response:

```json
{
  "status": "healthy",
  "service": "webapp",
  "timestamp": "2025-01-27T10:00:00.000Z",
  "uptime": 123.45
}
```

## 📦 Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm start
```

Production build includes:

- Server-side rendering (SSR)
- Static optimization
- Image optimization
- Code splitting
- Minification

## 🚢 Deployment Checklist

- [ ] Set `NEXT_PUBLIC_API_URL` environment variable
- [ ] Configure `DOMAIN` in `.env` for Traefik
- [ ] Set up SSL certificates (Let's Encrypt via Traefik)
- [ ] Run `npm run build` to verify build succeeds
- [ ] Test language switching works
- [ ] Verify all pages render correctly
- [ ] Check mobile responsiveness

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [next-intl](https://next-intl-docs.vercel.app/)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run linting: `npm run lint`
4. Format code: `npm run format`
5. Check types: `npm run type-check`
6. Test locally: `npm run dev`
7. Build production: `npm run build`
8. Create pull request

## 📝 License

Part of the Dating project. See main repository for license details.

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-27  
**Framework**: Next.js 15.5.4
