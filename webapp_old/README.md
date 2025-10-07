# 📱 Dating Mini App - Frontend

Telegram Mini App для сервиса знакомств Dating.

---

## 📂 Структура

```
webapp/
├── index.html          # Главная страница приложения
├── test.html           # Тестовая страница для проверки интеграции
├── css/
│   └── style.css      # Стили с Telegram Theme API
└── js/
    ├── app.js         # Основная логика и Telegram WebApp интеграция
    ├── discovery.js   # Поиск партнёров и свайпы
    └── navigation.js  # Навигация между экранами
```

---

## 🚀 Быстрый старт

### Локальный запуск

```bash
# Python HTTP сервер
cd webapp/
python3 -m http.server 8000
# Открыть: http://localhost:8000

# Или с Node.js
npx http-server -p 8000
```

### Тестирование в Telegram

1. **Запустить ngrok:**
```bash
ngrok http 8000
```

2. **Обновить URL в BotFather:**
```
/setmenubutton
<выберите бота>
<выберите "Edit menu button URL">
<вставьте https://xxxxx.ngrok.io URL>
```

3. **Открыть бота в Telegram и нажать кнопку Menu**

---

## 🧩 Ключевые файлы

### `index.html`

Основная страница с экранами:
- **Onboarding** - Приветствие
- **Profile Form** - Создание профиля
- **Success Screen** - Подтверждение создания
- **Discovery Screen** - Поиск партнёров (свайпы)
- **Matches Screen** - Взаимные симпатии
- **Favorites Screen** - Избранные профили
- **Profile Edit** - Редактирование своего профиля
- **Settings** - Настройки приватности

### `js/app.js`

Основная логика приложения:

```javascript
// Инициализация Telegram WebApp
initTelegramWebApp()

// Управление темой
applyTheme()
setupThemeListener()

// Управление UI
showOnboarding()
showLoading()
showError()

// Работа с формами
setupProfileForm()
handleProfileSubmit()
```

### `js/discovery.js`

Функционал поиска партнёров:

```javascript
// Загрузка карточек
loadDiscoveryCards()

// Действия
handleLike()
handlePass()
handleSuperlike()
handleAddFavorite()

// Фильтры
applyFilters()
```

### `js/navigation.js`

Навигация и управление экранами:

```javascript
// Показать экраны
showProfileEdit()
showSettings()
showDiscoveryFromNav()

// Управление навигацией
showBottomNav()
setActiveTab()
```

### `css/style.css`

Стили с использованием CSS переменных Telegram:

```css
:root {
  --tg-theme-bg-color: #ffffff;
  --tg-theme-text-color: #000000;
  --tg-theme-button-color: #2481cc;
  /* ... */
}
```

---

## 🎨 Telegram UI Components

### MainButton

Основная кнопка действия в нижней части экрана:

```javascript
// Показать кнопку
tg.MainButton.setText('Создать профиль');
tg.MainButton.show();
tg.MainButton.enable();

// Обработчик
tg.MainButton.onClick(handleSubmit);

// Скрыть
tg.MainButton.hide();

// Удалить обработчик перед добавлением нового
tg.MainButton.offClick(oldHandler);
```

**Используется на экранах:**
- Onboarding: "Начать знакомства"
- Profile Form: "Создать анкету"
- Profile Edit: "Сохранить изменения"

### BackButton

Кнопка назад в шапке:

```javascript
tg.BackButton.show();
tg.BackButton.onClick(handleBack);
tg.BackButton.hide();
```

### HapticFeedback

Тактильная обратная связь:

```javascript
// При нажатии на кнопки
tg.HapticFeedback.impactOccurred('medium');

// При успехе
tg.HapticFeedback.notificationOccurred('success');

// При ошибке
tg.HapticFeedback.notificationOccurred('error');
```

### Theme API

Автоматическая адаптация под тему Telegram:

```javascript
// Применение темы
function applyTheme() {
  const themeParams = tg.themeParams;
  for (const [key, cssVar] of Object.entries(themeMap)) {
    root.style.setProperty(cssVar, themeParams[key]);
  }
}

// Слушатель изменений
tg.onEvent('themeChanged', applyTheme);
```

---

## 🔌 Интеграция с Backend

### API Gateway

Все запросы через Gateway (порт 8080):

```javascript
const API_BASE_URL = window.location.protocol + '//' + 
                     window.location.hostname + ':8080';
```

### Аутентификация

```javascript
// Получить JWT токен
async function getAuthToken() {
  const response = await fetch(`${API_BASE_URL}/auth/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: tg.initData })
  });
  return (await response.json()).access_token;
}

// Использовать в запросах
fetch(`${API_BASE_URL}/api/profile`, {
  headers: { 'Authorization': `Bearer ${authToken}` }
});
```

### Микросервисы

| Endpoint | Сервис | Описание |
|----------|--------|----------|
| `/auth/*` | Auth Service (8081) | JWT токены |
| `/profiles/*` | Profile Service (8082) | CRUD профилей |
| `/discovery/*` | Discovery Service (8083) | Поиск и матчинг |
| `/media/*` | Media Service (8084) | Загрузка фото |
| `/chat/*` | Chat Service (8085) | Сообщения |

---

## 🧪 Тестирование

### Тестовая страница

Откройте `test.html` для проверки интеграции:

```bash
# Запустить сервер
python3 -m http.server 8000

# Открыть в браузере
open http://localhost:8000/test.html
```

Страница проверит:
- ✓ Загрузку Telegram WebApp SDK
- ✓ CSS переменные темы
- ✓ Доступность UI компонентов
- ✓ Информацию о платформе

### Ручное тестирование

1. **В браузере** - проверка вёрстки и логики
2. **В Telegram Desktop** - полная проверка с DevTools
3. **В Telegram Mobile** - финальная проверка на устройстве

### Отладка

```javascript
// Проверить состояние WebApp
console.log('Telegram WebApp:', tg);
console.log('User:', tg.initDataUnsafe.user);
console.log('Theme:', tg.colorScheme);
console.log('Platform:', tg.platform);

// Проверить MainButton
console.log('MainButton visible:', tg.MainButton.isVisible);
console.log('MainButton active:', tg.MainButton.isActive);
```

---

## 📦 Production Build

### Минификация

```bash
# JavaScript
npx terser js/app.js -c -m -o js/app.min.js
npx terser js/discovery.js -c -m -o js/discovery.min.js
npx terser js/navigation.js -c -m -o js/navigation.min.js

# CSS
npx csso css/style.css -o css/style.min.css
```

### Обновить index.html

```html
<!-- Production -->
<link rel="stylesheet" href="css/style.min.css">
<script src="js/app.min.js"></script>
<script src="js/discovery.min.js"></script>
<script src="js/navigation.min.js"></script>
```

### HTTPS

⚠️ **Важно:** Для production обязательно нужен HTTPS!

```bash
# Использовать Let's Encrypt через Traefik
# см. docker-compose.yml в корне проекта
```

---

## 🎯 Best Practices

### ✅ DO

- Использовать MainButton вместо обычных кнопок
- Добавлять Haptic Feedback на все действия
- Адаптироваться к теме Telegram автоматически
- Удалять старые обработчики перед добавлением новых
- Использовать `tg.showAlert()` вместо `alert()`
- Проверять `tg` перед использованием API

### ❌ DON'T

- Не использовать custom модальные окна (используйте tg.showPopup)
- Не блокировать UI долгими операциями
- Не забывать про Safe Areas (iPhone X+)
- Не игнорировать viewport changes
- Не хранить чувствительные данные в localStorage

---

## 🐛 Common Issues

### Проблема: MainButton не показывается

```javascript
// Решение: убедиться что вызваны show() и enable()
tg.MainButton.show();
tg.MainButton.enable();

// Проверить состояние
console.log('Visible:', tg.MainButton.isVisible);
console.log('Active:', tg.MainButton.isActive);
```

### Проблема: Тема не применяется

```javascript
// Решение: убедиться что applyTheme() вызывается после инициализации
setTimeout(applyTheme, 100);

// Или подписаться на событие
tg.ready(() => applyTheme());
```

### Проблема: WebApp не открывается в Telegram

1. Проверить что URL использует HTTPS (для production)
2. Проверить что URL правильно настроен в BotFather
3. Проверить что SDK загружается (`<script src="https://telegram.org/js/telegram-web-app.js"></script>`)

---

## 📚 Дополнительная документация

- 🚀 [Quick Start Guide](../docs/MINIAPP_QUICK_START.md)
- 📱 [Architecture Documentation](../docs/MINIAPP_ARCHITECTURE.md)
- 🔌 [Port Mapping](../docs/PORT_MAPPING.md)
- 📊 [Monitoring Setup](../docs/MONITORING_SETUP.md)

### Official Resources

- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [WebApp Demo](https://t.me/DurgerKingBot)

---

## 🔄 Changelog

### v1.3.0 (2025-01-06)

- ✨ Добавлена поддержка Telegram MainButton
- ✨ Добавлена поддержка BackButton
- ✨ Улучшена интеграция с Theme API
- ✨ Добавлена поддержка viewport changes
- ✨ Расширены CSS переменные для темы
- 📝 Добавлена полная документация
- 🧪 Добавлена тестовая страница

### v1.2.0

- ✨ Добавлен экран редактирования профиля
- ✨ Добавлена нижняя навигация
- ✨ Улучшена работа с фото

### v1.1.0

- ✨ Добавлен поиск партнёров (discovery)
- ✨ Добавлены фильтры
- ✨ Добавлена система матчинга

### v1.0.0

- 🎉 Первый релиз
- ✨ Создание профиля
- ✨ Интеграция с Telegram WebApp

---

**Version:** 1.3.0  
**Last Updated:** 2025-01-06  
**Maintainer:** Dating Team

---

*Для вопросов и предложений создавайте Issues на GitHub*
