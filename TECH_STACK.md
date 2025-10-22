# 🏗️ Технологический стек проекта

## Backend
- **Python 3.11+** - основной язык
- **aiohttp** - асинхронный HTTP сервер
- **SQLAlchemy 2.0+** - ORM
- **PostgreSQL 15** - основная БД
- **Alembic** - миграции БД
- **PyJWT** - JWT токены
- **aiogram 3.3** - Telegram Bot API

## Frontend
- **Vanilla HTML/CSS/JS** - основной фронтенд
- **Telegram WebApp SDK** - интеграция с Telegram
- **Nginx** - статический сервер

## Infrastructure
- **Docker + Docker Compose** - контейнеризация
- **Traefik v2.11** - reverse proxy и SSL
- **Let's Encrypt** - SSL сертификаты

## Monitoring
- **Prometheus** - метрики
- **Grafana** - визуализация
- **Loki** - логи
- **cAdvisor** - метрики контейнеров

## Security
- **JWT** - аутентификация
- **bcrypt** - хеширование паролей
- **CORS** - политики безопасности
- **Rate Limiting** - защита от DDoS

## AI/ML
- **NudeNet 2.x** - NSFW детекция
- **ONNX Runtime** - ML inference
- **Pillow** - обработка изображений

## 🚫 НЕ ИСПОЛЬЗОВАТЬ
- React/Vue/Angular - только vanilla JS
- Next.js/Nuxt.js - только статические файлы
- Redis - только PostgreSQL
- MongoDB - только PostgreSQL
- Express.js - только Python aiohttp
- Node.js - только Python

## 📋 Принципы разработки
1. **Микросервисная архитектура** - каждый сервис независим
2. **Централизованный доступ к данным** - только через Data Service
3. **Telegram-first** - все взаимодействие через Telegram
4. **Безопасность** - JWT, HTTPS, валидация
5. **Мониторинг** - полная наблюдаемость системы
