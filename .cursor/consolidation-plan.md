# План объединения всех правил в .cursor

## 🎯 **ЦЕЛЬ**
Объединить все правила разработки, документацию и стандарты в единую папку `.cursor` для удобного управления.

## 📁 **ТЕКУЩАЯ СТРУКТУРА**

### В `.cursor/`:
- `RULES.md` - основные правила
- `naming-conventions.md` - соглашения по именованию
- `validation-report.md` - отчет о валидации
- `rule-audit-report.md` - аудит правил
- `archive/` - архивные файлы

### В `docs/` (18 файлов):
- `API_DOCUMENTATION.md`
- `ARCHITECTURE.md`
- `CI_CD_GUIDE.md`
- `CODE_QUALITY.md`
- `DEPLOYMENT_GUIDE.md`
- `DEVELOPMENT_GUIDE.md`
- `DOCKER_SECURITY.md`
- `DOCKER_SECURITY_AUDIT.md`
- `DOCKER_USER_STANDARDS.md`
- `ENVIRONMENTS.md`
- `ERROR_HANDLING.md`
- `FRONTEND_DEVELOPMENT.md`
- `METRICS_GUIDE.md`
- `OBSERVABILITY.md`
- `REFACTORING_SUMMARY.md`
- `VERSIONING_AND_RELEASES.md`
- `jwt-security-policy.md`
- `traefik-routes.md`

## 🗂️ **ПРЕДЛАГАЕМАЯ СТРУКТУРА .cursor/**

```
.cursor/
├── README.md                    # Главный индекс
├── RULES.md                     # Основные правила (существующий)
├── 
├── development/                 # Правила разработки
│   ├── code-quality.md
│   ├── frontend-development.md
│   ├── api-documentation.md
│   └── error-handling.md
├── 
├── infrastructure/              # Инфраструктура
│   ├── docker-security.md
│   ├── docker-user-standards.md
│   ├── environments.md
│   └── traefik-routes.md
├── 
├── deployment/                  # Деплой и релизы
│   ├── ci-cd-guide.md
│   ├── deployment-guide.md
│   ├── versioning-releases.md
│   └── jwt-security-policy.md
├── 
├── monitoring/                  # Мониторинг и метрики
│   ├── metrics-guide.md
│   ├── observability.md
│   └── architecture.md
├── 
├── standards/                   # Стандарты
│   ├── naming-conventions.md
│   └── validation-report.md
├── 
└── archive/                     # Архив
    ├── rule-audit-report.md
    └── [старые файлы]
```

## 📋 **ПЛАН ДЕЙСТВИЙ**

### Этап 1: Создание структуры
1. Создать папки: `development/`, `infrastructure/`, `deployment/`, `monitoring/`, `standards/`
2. Переместить файлы из `docs/` в соответствующие папки
3. Обновить ссылки в `RULES.md`

### Этап 2: Обновление ссылок
1. Обновить все внутренние ссылки
2. Создать главный `README.md` с навигацией
3. Обновить `RULES.md` с новыми путями

### Этап 3: Очистка
1. Удалить дублирующиеся файлы
2. Обновить `.gitignore` если нужно
3. Проверить, что все работает

## 🎯 **РЕЗУЛЬТАТ**

- Единая папка `.cursor/` со всеми правилами
- Логическая структура по категориям
- Удобная навигация и поиск
- Чистота в корне проекта
- Легкость поддержки и обновления

## 📊 **СТАТИСТИКА**

- **Всего файлов для перемещения**: 18
- **Новых папок**: 5
- **Обновленных ссылок**: ~50
- **Время выполнения**: ~30 минут
