# 👨‍💻 Development Guide

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [API Development](#api-development)
- [Frontend Development](#frontend-development)
- [Database Development](#database-development)
- [Debugging](#debugging)
- [Contributing](#contributing)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** - Backend development
- **Node.js 20+** - Frontend development
- **Docker & Docker Compose** - Containerization
- **Git** - Version control
- **VS Code** (recommended) - IDE

### Quick Setup

```bash
# Clone repository
git clone <repository-url>
cd dating

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start development environment
docker compose up -d db traefik

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies
cd webapp
npm install
cd ..

# Run tests
pytest

# Start development
npm run dev  # Frontend
python -m services.auth.main  # Backend service
```

---

## 📁 Project Structure

```
dating/
├── bot/                    # Telegram Bot
│   ├── main.py            # Bot entry point
│   ├── config.py          # Configuration
│   ├── db.py              # Database models
│   └── repository.py      # Data access layer
├── core/                   # Shared utilities
│   └── utils/             # Common utilities
│       ├── logging.py     # Logging configuration
│       ├── security.py    # Security utilities
│       └── validation.py  # Data validation
├── services/               # Microservices
│   ├── auth/              # Authentication service
│   ├── profile/           # Profile management
│   ├── discovery/         # Matching algorithm
│   ├── media/             # File handling
│   ├── chat/              # Real-time messaging
│   ├── admin/             # Admin panel
│   ├── notification/      # Push notifications
│   └── data/              # Centralized data access
├── gateway/                # API Gateway
│   └── main.py            # Request routing
├── webapp/                 # Next.js Frontend
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   └── package.json       # Dependencies
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── migrations/             # Database migrations
├── monitoring/             # Monitoring configuration
├── scripts/                # Utility scripts
└── docs/                   # Documentation
```

---

## 🛠️ Development Environment

### Local Development Setup

#### 1. Backend Services

```bash
# Start infrastructure
docker compose up -d db traefik

# Run individual services
cd services/auth
python -m services.auth.main

# Or run all services
docker compose up -d
```

#### 2. Frontend Development

```bash
cd webapp

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

#### 3. Database Development

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Access database
docker compose exec db psql -U dating -d dating
```

### Development Tools

#### VS Code Extensions

Recommended extensions for development:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json"
  ]
}
```

#### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 📝 Coding Standards

### Python Code Style

#### Black Formatting

```bash
# Format code
black .

# Check formatting
black --check .
```

#### Import Organization

```python
# Standard library imports
import os
import logging
from typing import Dict, List

# Third-party imports
from aiohttp import web
from sqlalchemy import select

# Local imports
from core.utils.logging import configure_logging
from bot.repository import ProfileRepository
```

#### Type Hints

```python
from typing import Dict, List, Optional, Any

async def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile by ID."""
    pass

def process_data(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Process data and return statistics."""
    pass
```

#### Error Handling

```python
import logging

logger = logging.getLogger(__name__)

async def handle_request(request: web.Request) -> web.Response:
    try:
        # Process request
        result = await process_data(request)
        return web.json_response(result)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)
```

### TypeScript/React Code Style

#### ESLint Configuration

```json
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "prefer-const": "error"
  }
}
```

#### Component Structure

```typescript
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface ProfileProps {
  userId: number;
  onUpdate?: (profile: Profile) => void;
}

export function Profile({ userId, onUpdate }: ProfileProps) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/profiles/${userId}`);
      const data = await response.json();
      setProfile(data);
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!profile) return <div>Profile not found</div>;

  return (
    <div className="profile">
      <h1>{profile.name}</h1>
      <p>{profile.bio}</p>
    </div>
  );
}
```

---

## 🧪 Testing Guidelines

### Test Structure

#### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, Mock
from services.auth.main import validate_telegram_init_data

@pytest.mark.asyncio
async def test_validate_telegram_init_data_success():
    """Test successful Telegram initData validation."""
    # Arrange
    request = Mock()
    request.json = AsyncMock(return_value={
        "init_data": "valid_init_data",
        "bot_token": "valid_bot_token"
    })
    
    # Act
    response = await validate_telegram_init_data(request)
    
    # Assert
    assert response.status == 200
    data = await response.json()
    assert "token" in data
    assert "user_id" in data
```

#### Integration Tests

```python
import pytest
from aiohttp import web, ClientSession
from aiohttp.test_utils import make_mocked_request

@pytest.mark.asyncio
async def test_profile_creation_flow():
    """Test complete profile creation flow."""
    # Test profile creation
    async with ClientSession() as session:
        async with session.post(
            "http://localhost:8082/profiles",
            json=profile_data,
            headers={"Authorization": f"Bearer {token}"}
        ) as response:
            assert response.status == 201
            data = await response.json()
            assert data["user_id"] == user_id
```

#### End-to-End Tests

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_user_onboarding_flow():
    """Test complete user onboarding flow."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to onboarding
        await page.goto("http://localhost:3000/ru/onboarding")
        
        # Fill form
        await page.fill('[data-testid="name"]', "John Doe")
        await page.fill('[data-testid="bio"]', "Looking for someone special")
        
        # Submit form
        await page.click('[data-testid="submit"]')
        
        # Verify success
        await page.wait_for_selector('[data-testid="success"]')
        
        await browser.close()
```

### Test Commands

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=bot --cov=services --cov-report=html

# Run specific test
pytest tests/unit/test_auth.py::test_validate_token

# Run tests in parallel
pytest -n auto
```

---

## 🔌 API Development

### Creating New Endpoints

#### 1. Define Route Handler

```python
async def get_user_stats(request: web.Request) -> web.Response:
    """Get user statistics.
    
    GET /users/{user_id}/stats
    """
    try:
        user_id = int(request.match_info["user_id"])
        
        # Get stats from data service
        data_service_url = request.app["data_service_url"]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/users/{user_id}/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    return web.json_response(stats)
                else:
                    return web.json_response({"error": "User not found"}, status=404)
                    
    except ValueError:
        return web.json_response({"error": "Invalid user_id"}, status=400)
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
```

#### 2. Register Route

```python
def create_app(config: dict) -> web.Application:
    """Create and configure the application."""
    app = web.Application()
    app["config"] = config
    
    # Add routes
    app.router.add_get("/users/{user_id}/stats", get_user_stats)
    app.router.add_get("/health", health_check)
    
    return app
```

#### 3. Add to API Gateway

```python
# In gateway/main.py
async def route_user_stats(request: web.Request) -> web.Response:
    """Route user stats requests to profile service."""
    return await proxy_request(request, "http://profile-service:8082")

# Register route
app.router.add_get("/users/{user_id}/stats", route_user_stats)
```

### API Documentation

#### OpenAPI Specification

```python
from aiohttp_swagger import setup_swagger

def create_app(config: dict) -> web.Application:
    app = web.Application()
    
    # Add routes
    app.router.add_get("/users/{user_id}/stats", get_user_stats)
    
    # Setup Swagger documentation
    setup_swagger(app, swagger_url="/api/docs")
    
    return app
```

#### Request/Response Examples

```python
async def get_user_stats(request: web.Request) -> web.Response:
    """
    Get user statistics.
    
    ---
    tags:
    - users
    summary: Get user statistics
    description: Retrieve comprehensive statistics for a specific user
    parameters:
    - name: user_id
      in: path
      required: true
      schema:
        type: integer
      description: User ID
    responses:
      200:
        description: User statistics retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                total_matches:
                  type: integer
                total_likes:
                  type: integer
                profile_views:
                  type: integer
      404:
        description: User not found
      500:
        description: Internal server error
    """
    # Implementation...
```

---

## 🎨 Frontend Development

### Component Development

#### Component Structure

```typescript
// components/ProfileCard.tsx
import { useState } from 'react';
import { Profile } from '@/types/profile';

interface ProfileCardProps {
  profile: Profile;
  onLike?: (profileId: number) => void;
  onPass?: (profileId: number) => void;
}

export function ProfileCard({ profile, onLike, onPass }: ProfileCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleLike = async () => {
    if (!onLike) return;
    
    setIsLoading(true);
    try {
      await onLike(profile.id);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="profile-card">
      <img src={profile.photos[0]} alt={profile.name} />
      <h2>{profile.name}</h2>
      <p>{profile.bio}</p>
      <div className="actions">
        <button 
          onClick={handlePass}
          disabled={isLoading}
          className="pass-button"
        >
          Pass
        </button>
        <button 
          onClick={handleLike}
          disabled={isLoading}
          className="like-button"
        >
          Like
        </button>
      </div>
    </div>
  );
}
```

#### Custom Hooks

```typescript
// hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/auth/verify');
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        router.push('/login');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      router.push('/login');
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
    router.push('/login');
  };

  return { user, loading, logout };
}
```

### State Management

#### TanStack Query Setup

```typescript
// providers/query-provider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 3,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

#### Data Fetching

```typescript
// hooks/useProfiles.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await fetch('/api/profiles');
      return response.json();
    },
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (profileData: CreateProfileData) => {
      const response = await fetch('/api/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData),
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}
```

---

## 🗄️ Database Development

### Model Definition

```python
# bot/db.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(DateTime, nullable=False)
    gender = Column(String(20), nullable=False)
    city = Column(String(100), nullable=False)
    bio = Column(Text)
    interests = Column(Text)  # JSON string
    goal = Column(String(50))
    orientation = Column(String(20))
    height_cm = Column(Integer)
    education = Column(String(100))
    work = Column(String(100))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### Repository Pattern

```python
# bot/repository.py
from typing import List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db import Profile, User

class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_profile_by_user_id(self, user_id: int) -> Optional[Profile]:
        """Get profile by user ID."""
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_profile(self, profile_data: dict) -> Profile:
        """Create new profile."""
        profile = Profile(**profile_data)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
    
    async def find_candidates(
        self, 
        user_id: int, 
        limit: int = 10, 
        cursor: int = None,
        **filters
    ) -> Tuple[List[Profile], Optional[int]]:
        """Find candidate profiles for matching."""
        query = select(Profile).where(Profile.user_id != user_id)
        
        # Apply filters
        if filters.get('age_min'):
            query = query.where(Profile.birth_date <= calculate_birth_date(filters['age_min']))
        if filters.get('age_max'):
            query = query.where(Profile.birth_date >= calculate_birth_date(filters['age_max']))
        if filters.get('gender'):
            query = query.where(Profile.gender == filters['gender'])
        if filters.get('city'):
            query = query.where(Profile.city == filters['city'])
        
        # Pagination
        if cursor:
            query = query.where(Profile.id > cursor)
        
        query = query.limit(limit + 1)
        
        result = await self.session.execute(query)
        profiles = result.scalars().all()
        
        next_cursor = None
        if len(profiles) > limit:
            next_cursor = profiles[-1].id
            profiles = profiles[:-1]
        
        return profiles, next_cursor
```

### Migration Creation

```python
# migrations/versions/007_add_profile_verification.py
"""Add profile verification

Revision ID: 007
Revises: 006
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    # Add verification columns
    op.add_column('profiles', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('profiles', sa.Column('verified_at', sa.DateTime(), nullable=True))
    
    # Create index for verified profiles
    op.create_index('ix_profiles_is_verified', 'profiles', ['is_verified'])

def downgrade():
    op.drop_index('ix_profiles_is_verified', table_name='profiles')
    op.drop_column('profiles', 'verified_at')
    op.drop_column('profiles', 'is_verified')
```

---

## 🐛 Debugging

### Backend Debugging

#### Logging Configuration

```python
# core/utils/logging.py
import logging
import sys
from typing import Optional

def configure_logging(service_name: str, level: str = "INFO") -> None:
    """Configure structured logging for a service."""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Service-specific logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
```

#### Debug Logging

```python
import logging

logger = logging.getLogger(__name__)

async def process_request(request: web.Request) -> web.Response:
    logger.debug(f"Processing request: {request.method} {request.path}")
    
    try:
        # Process request
        result = await handle_request(request)
        logger.info(f"Request processed successfully: {request.path}")
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Request failed: {request.path}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)
```

### Frontend Debugging

#### React DevTools

```typescript
// Enable React DevTools in development
if (process.env.NODE_ENV === 'development') {
  import('react-dom/client').then(({ createRoot }) => {
    // Development-specific code
  });
}
```

#### Debug Logging

```typescript
// utils/debug.ts
export const debug = {
  log: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEBUG] ${message}`, data);
    }
  },
  
  error: (message: string, error?: Error) => {
    if (process.env.NODE_ENV === 'development') {
      console.error(`[ERROR] ${message}`, error);
    }
  }
};

// Usage
debug.log('User profile loaded', profile);
debug.error('Failed to load profile', error);
```

### Database Debugging

#### Query Logging

```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or in alembic.ini
[alembic]
# ... other settings ...
sqlalchemy.echo = True
```

#### Database Inspection

```python
# Inspect database schema
from sqlalchemy import inspect

def inspect_database(engine):
    inspector = inspect(engine)
    
    # List all tables
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    # Inspect specific table
    columns = inspector.get_columns('profiles')
    for column in columns:
        print(f"Column: {column['name']}, Type: {column['type']}")
```

---

## 🤝 Contributing

### Development Workflow

#### 1. Fork and Clone

```bash
# Fork repository on GitHub
git clone https://github.com/your-username/dating.git
cd dating
git remote add upstream https://github.com/original-repo/dating.git
```

#### 2. Create Feature Branch

```bash
git checkout -b feature/new-feature
```

#### 3. Make Changes

```bash
# Make your changes
# Write tests
# Update documentation

# Run tests
pytest
npm test

# Format code
black .
npm run format
```

#### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature

- Add new API endpoint
- Update documentation
- Add tests

Closes #123"
```

#### 5. Push and Create PR

```bash
git push origin feature/new-feature
# Create pull request on GitHub
```

### Commit Message Format

```
type(scope): description

Body of the commit message explaining what and why.

Closes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

### Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Peer Review**: At least one team member reviews the code
3. **Testing**: Manual testing of new features
4. **Documentation**: Update relevant documentation
5. **Merge**: Merge after approval

### Issue Reporting

When reporting issues, include:

1. **Environment**: OS, Python version, Node.js version
2. **Steps to Reproduce**: Clear steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Logs**: Relevant error logs
6. **Screenshots**: If applicable

---

*Last updated: January 2025*
