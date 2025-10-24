#!/bin/bash

echo "🧹 Creating clean Git history..."

# Create backup branch
echo "📦 Creating backup branch..."
git branch backup-full-history

# Create a new orphan branch (no history)
echo "🆕 Creating new orphan branch 'clean-main'..."
git checkout --orphan clean-main

# Add all current files
echo "📁 Adding all current files..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "feat: Complete Dating App Implementation

BREAKING CHANGE: Clean history with all features implemented

FEATURES IMPLEMENTED:
✅ Telegram Bot Integration
✅ Vue 3 + Vite Frontend
✅ Microservices Architecture
✅ Admin Panel
✅ Real-time Chat (WebSocket)
✅ User Profiles & Discovery
✅ Photo Upload & NSFW Detection
✅ Profile Verification
✅ Settings & Preferences
✅ Push Notifications
✅ Monitoring & Health Checks
✅ CI/CD Pipeline (GitHub Actions)
✅ Docker & Docker Compose
✅ Database Migrations (Alembic)
✅ Security & Authentication
✅ Rate Limiting
✅ Comprehensive Testing
✅ Documentation & Rules

TECHNICAL STACK:
- Backend: Python (aiohttp, FastAPI)
- Frontend: Vue 3, Vite, Pinia
- Database: PostgreSQL
- Cache: Redis
- Message Queue: Redis
- Monitoring: Prometheus, Grafana, Loki
- Container: Docker, Docker Compose
- CI/CD: GitHub Actions
- Reverse Proxy: Traefik
- Web Server: Nginx

This commit represents the complete, production-ready dating application
with all features, monitoring, and deployment infrastructure."

echo "✅ Clean history created!"
echo "📋 Next steps:"
echo "1. Review the new branch: git log --oneline"
echo "2. If satisfied, replace main: git branch -D main && git branch -m clean-main main"
echo "3. Force push to GitHub: git push origin main --force"
echo "4. Update server: git pull origin main --force"
