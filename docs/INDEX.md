# 📚 Documentation Index

Полное оглавление документации проекта Dating.

---

## 🚀 Начало работы

### Для новых разработчиков
- **[Getting Started](GETTING_STARTED.md)** - Быстрый старт и первые шаги
- **[README.md](../README.md)** - Общее описание проекта
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Как внести вклад в проект

---

## 🏗️ Архитектура и Дизайн

### Общая архитектура
- **[README.md - Архитектура](../README.md#архитектура)** - Обзор микросервисной архитектуры
- **[Thin Client Architecture](THIN_CLIENT_ARCHITECTURE.md)** - Архитектура тонкого клиента
- **[Bot Architecture Change](BOT_ARCHITECTURE_CHANGE.md)** - Изменения в архитектуре бота

### Frontend
- **[Mini App Architecture](MINIAPP_ARCHITECTURE.md)** - Архитектура Telegram Mini App (legacy Vanilla JS)
- **[Mini App Quick Start](MINIAPP_QUICK_START.md)** - Быстрый старт с Mini App
- **[Mini App UI Improvements](MINIAPP_UI_IMPROVEMENTS.md)** - Улучшения UI
- **[WebApp README](../webapp/README.md)** - Next.js 15 WebApp (основная версия)

### Backend
- **[API Gateway Routes](API_GATEWAY_ROUTES.md)** - Маршруты и endpoints API Gateway
- **[API Contract Verification](API_CONTRACT_VERIFICATION.md)** - Проверка контрактов API
- **[Port Mapping](PORT_MAPPING.md)** - Карта портов всех сервисов

---

## 🔧 Разработка

### Настройка и запуск
- **[Getting Started](GETTING_STARTED.md)** - Полное руководство по настройке
- **[.env.example](../.env.example)** - Пример конфигурации окружения

### Тестирование
- **[Test Refactoring 2024](TEST_REFACTORING_2024.md)** - Обновление тестов (380+ тестов)
- **[tests/README.md](../tests/README.md)** - Документация по тестам

### Code Quality
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Стандарты кода и процесс разработки

---

## 🚢 Деплой и DevOps

### CI/CD
- **[CI/CD Guide](CI_CD_GUIDE.md)** - Полное руководство по CI/CD с GitHub Actions
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Чек-лист для деплоя

### Troubleshooting
- **[Deployment Troubleshooting](DEPLOYMENT_TROUBLESHOOTING.md)** - Решение проблем при деплое
- **[README.md - Решение проблем](../README.md#решение-проблем)** - Общие проблемы и решения

---

## 📊 Мониторинг

### Настройка мониторинга
- **[Monitoring Setup](MONITORING_SETUP.md)** - Prometheus, Grafana, Loki v3.0
- **[Monitoring v3 Migration](MONITORING_V3_MIGRATION.md)** - Миграция на v3.0
- **[README.md - Мониторинг](../README.md#мониторинг)** - Обзор мониторинга

---

## 👨‍💼 Администрирование

### Административная панель
- **[Admin Panel Guide](ADMIN_PANEL_GUIDE.md)** - Полное руководство по админ панели
- **[services/admin/README.md](../services/admin/README.md)** - Admin Service документация

---

## 🔐 Безопасность

### Документация по безопасности
- **[SECURITY.md](../SECURITY.md)** - Политика безопасности, отчет о уязвимостях
- **[webapp/docs/SECURITY.md](../webapp/docs/SECURITY.md)** - Безопасность WebApp
- **[README.md - Безопасность](../README.md#безопасность)** - Обзор функций безопасности

---

## 📋 Планы и История

### Планирование
- **[ROADMAP.md](../ROADMAP.md)** - Планируемые функции и текущий статус
- **[CHANGELOG.md](../CHANGELOG.md)** - История изменений проекта

---

## 🗂️ Архив

### Исторические документы
- **[docs/archive/](archive/README.md)** - Архив завершенных summary и bug fix документов
  - Bug fixes (порты 5432, 8080)
  - Deployment fixes
  - Feature summaries (Admin Panel, Integration, MiniApp, Monitoring)
  - Refactoring summaries

---

## 📖 Специфичные темы

### Рефакторинг и миграции
- **[Refactoring Summary](REFACTORING_SUMMARY.md)** - Обзор рефакторинга кодовой базы
- **[Timezone Fix Migration Guide](TIMEZONE_FIX_MIGRATION_GUIDE.md)** - Исправление timezone
- **[Profile Fields Mapping](PROFILE_FIELDS_MAPPING.md)** - Маппинг полей профиля

---

## 🌐 Внешние ресурсы

### Документация используемых технологий
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Python Documentation](https://docs.python.org/3.12/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## 📞 Поддержка

### Получить помощь
- 🐛 [GitHub Issues](https://github.com/erliona/dating/issues) - Сообщить о баге или запросить функцию
- 💬 [GitHub Discussions](https://github.com/erliona/dating/discussions) - Обсуждения и вопросы
- 📧 Email: support@example.com

### Отчет о уязвимостях
- 🔒 Не создавайте публичные issues
- 📧 Напишите на security@example.com
- 📄 См. [SECURITY.md](../SECURITY.md)

---

## 📊 Статистика проекта

- **Язык**: Python 3.11+ (Docker: 3.11, CI: 3.12)
- **Framework**: Next.js 15, React 19, aiogram 3.x
- **Архитектура**: 7 микросервисов
- **Тесты**: 381 автоматических тестов (362 passed, 95.0%)
- **Строк кода**: ~17,000 строк Python
- **Документация**: 18+ документов

---

**Последнее обновление**: Январь 2025  
**Версия документации**: 2.0
