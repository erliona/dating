# 📱 Mini App Architecture Documentation

## Обзор

Dating Mini App - это Progressive Web App (PWA), полностью интегрированное в экосистему Telegram через [Telegram WebApp API](https://core.telegram.org/bots/webapps). Приложение следует принципам микросервисной архитектуры и использует нативные компоненты Telegram UI для обеспечения единого пользовательского опыта.

---

## 🏗️ Архитектура Frontend

### Структура файлов

```
webapp/
├── index.html           # Главная страница приложения
├── css/
│   └── style.css       # Стили с использованием Telegram Theme API
└── js/
    ├── app.js          # Основная логика, интеграция с Telegram WebApp
    ├── discovery.js    # Функциональность поиска и свайпов
    └── navigation.js   # Навигация и управление экранами
```

### Компоненты приложения

#### 1. **Telegram WebApp Integration (`app.js`)**

Основная интеграция с Telegram WebApp SDK:

```javascript
// Инициализация
function initTelegramWebApp() {
  tg = window.Telegram.WebApp;
  
  // Настройка UI
  tg.expand();                                    // Полноэкранный режим
  tg.setHeaderColor('secondary_bg_color');       // Цвет шапки
  tg.setBackgroundColor('bg_color');             // Цвет фона
  tg.enableClosingConfirmation();                 // Подтверждение закрытия
  
  // Управление кнопками
  tg.MainButton.setText('Текст кнопки');
  tg.MainButton.show();
  tg.BackButton.onClick(handleBackButton);
  
  // Тема
  applyTheme();
}
```

**Используемые API Telegram:**
- `MainButton` - Основная кнопка действия внизу экрана
- `BackButton` - Кнопка назад в шапке
- `HapticFeedback` - Тактильная обратная связь
- `themeParams` - Параметры темы для стилизации
- `initData` - Данные пользователя для аутентификации

#### 2. **Theme System**

Приложение адаптируется под темы Telegram (светлая/тёмная):

```css
:root {
  /* Переменные, синхронизированные с Telegram */
  --tg-theme-bg-color: #ffffff;
  --tg-theme-text-color: #000000;
  --tg-theme-button-color: #2481cc;
  --tg-theme-button-text-color: #ffffff;
  /* ... */
}
```

Динамическое применение темы:

```javascript
function applyTheme() {
  const themeParams = tg.themeParams;
  const root = document.documentElement;
  
  for (const [tgParam, cssVar] of Object.entries(themeMap)) {
    if (themeParams[tgParam]) {
      root.style.setProperty(cssVar, themeParams[tgParam]);
    }
  }
}

// Слушатель изменения темы
tg.onEvent('themeChanged', () => {
  applyTheme();
  triggerHaptic('impact', 'light');
});
```

#### 3. **Navigation System (`navigation.js`)**

Управление экранами и навигацией:

```javascript
// Экраны приложения
const screens = [
  'onboarding',          // Приветствие
  'profile-form',        // Создание профиля
  'success-screen',      // Успешное создание
  'discovery-screen',    // Поиск партнёров
  'matches-screen',      // Список матчей
  'favorites-screen',    // Избранное
  'profile-edit-screen', // Редактирование профиля
  'settings-screen'      // Настройки
];

// Нижняя навигация (Bottom Navigation)
// - Профиль
// - Знакомства
// - Настройки
```

#### 4. **Discovery & Swipes (`discovery.js`)**

Функциональность поиска и матчинга:

```javascript
// Карточная система
- Загрузка профилей с API
- Свайпы (touch/mouse events)
- Фильтры (возраст, расстояние, цели)
- Действия: Лайк, Дизлайк, Суперлайк, Избранное
```

---

## 🔗 Интеграция с Backend

### API Gateway

Все запросы идут через API Gateway (`http://gateway:8080`):

```javascript
const API_BASE_URL = window.location.protocol + '//' + 
                     window.location.hostname + ':8080';

// Аутентификация через JWT
const response = await fetch(`${API_BASE_URL}/api/profile`, {
  headers: {
    'Authorization': `Bearer ${authToken}`
  }
});
```

### Микросервисы

| Сервис | Порт | Эндпоинт | Описание |
|--------|------|----------|----------|
| Auth Service | 8081 | `/auth/*` | JWT токены, валидация Telegram данных |
| Profile Service | 8082 | `/profiles/*` | CRUD операции с профилями |
| Discovery Service | 8083 | `/discovery/*` | Поиск, матчинг, фильтры |
| Media Service | 8084 | `/media/*` | Загрузка и обработка фото |
| Chat Service | 8085 | `/chat/*` | Сообщения между матчами |

### Аутентификация

```javascript
// Получение JWT токена
async function getAuthToken() {
  const response = await fetch(`${API_BASE_URL}/api/auth/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      init_data: tg.initData  // Telegram WebApp init data
    })
  });
  
  const data = await response.json();
  return data.access_token;
}
```

---

## 🎨 UI Components (Telegram Native)

### 1. MainButton

Основная кнопка действия внизу экрана:

```javascript
// Показать кнопку
tg.MainButton.setText('Создать анкету');
tg.MainButton.show();
tg.MainButton.enable();
tg.MainButton.onClick(handleSubmit);

// Скрыть кнопку
tg.MainButton.hide();

// Удалить обработчик
tg.MainButton.offClick(handleSubmit);
```

**Использование:**
- Онбординг: "Начать знакомства"
- Форма профиля: "Создать анкету"
- Редактирование: "Сохранить изменения"

### 2. BackButton

Кнопка назад в шапке:

```javascript
tg.BackButton.show();
tg.BackButton.onClick(handleBack);
tg.BackButton.hide();
```

### 3. HapticFeedback

Тактильная обратная связь:

```javascript
// Impact feedback (лёгкое, среднее, сильное)
tg.HapticFeedback.impactOccurred('light');
tg.HapticFeedback.impactOccurred('medium');
tg.HapticFeedback.impactOccurred('heavy');

// Notification feedback
tg.HapticFeedback.notificationOccurred('success');
tg.HapticFeedback.notificationOccurred('error');
tg.HapticFeedback.notificationOccurred('warning');

// Selection feedback
tg.HapticFeedback.selectionChanged();
```

**Применение:**
- Нажатия кнопок: `impact/medium`
- Успешные действия: `notification/success`
- Ошибки: `notification/error`
- Свайпы: `impact/light`

### 4. Alert & Confirm

Модальные окна:

```javascript
// Alert
tg.showAlert('Сообщение для пользователя');

// Confirm
tg.showConfirm('Вы уверены?', (confirmed) => {
  if (confirmed) {
    // Пользователь подтвердил
  }
});

// Popup с кнопками
tg.showPopup({
  title: 'Заголовок',
  message: 'Текст',
  buttons: [
    { id: 'cancel', type: 'cancel' },
    { id: 'confirm', type: 'default', text: 'OK' }
  ]
}, (buttonId) => {
  console.log('Нажата кнопка:', buttonId);
});
```

---

## 📊 Data Flow

### 1. Создание профиля

```
User Input → Validation → Upload Photos → Create Profile → JWT Auth → Success
     ↓            ↓              ↓              ↓            ↓         ↓
  HTML Form   JavaScript   Media Service  Profile Service  Auth     Discovery
```

### 2. Discovery (Поиск партнёров)

```
Discovery Screen → Load Cards → Filter/Sort → Swipe Actions → Matching
        ↓              ↓            ↓              ↓            ↓
   navigation.js  discovery.js  Filters API   Actions API  Match API
```

### 3. Аутентификация

```
Telegram Init Data → Validate HMAC → Create JWT → Store Token → API Calls
         ↓                ↓             ↓            ↓           ↓
   WebApp SDK       Auth Service    JWT Token   localStorage  Headers
```

---

## 🔐 Security

### 1. Telegram Data Validation

```javascript
// Все Telegram init_data валидируются на бэкенде
// через HMAC с использованием Bot Token
const isValid = validateTelegramInitData(initData, BOT_TOKEN);
```

### 2. JWT Authentication

```javascript
// JWT токен в каждом запросе
headers: {
  'Authorization': `Bearer ${authToken}`
}

// Refresh при истечении (401)
if (response.status === 401) {
  authToken = await getAuthToken();
  // Retry request
}
```

### 3. HTTPS Everywhere

- Все запросы через HTTPS
- WebApp должен быть на HTTPS для production
- Let's Encrypt сертификаты

---

## 📱 Responsive Design

### Viewport

```html
<meta name="viewport" 
      content="width=device-width, initial-scale=1.0, 
               maximum-scale=1.0, user-scalable=no, 
               viewport-fit=cover">
```

### Safe Areas

```css
html {
  padding: env(safe-area-inset-top) 
           env(safe-area-inset-right) 
           env(safe-area-inset-bottom) 
           env(safe-area-inset-left);
}

.bottom-nav {
  padding-bottom: max(8px, env(safe-area-inset-bottom));
}
```

### Adaptive Heights

```javascript
tg.viewportHeight         // Текущая высота viewport
tg.viewportStableHeight   // Стабильная высота (без клавиатуры)
```

---

## 🚀 Performance

### 1. Lazy Loading

```javascript
// Загрузка карточек порционно
async function loadDiscoveryCards() {
  const params = new URLSearchParams({ limit: '10' });
  if (cursor) params.append('cursor', cursor);
  // ...
}
```

### 2. Caching

```javascript
// LocalStorage для кэширования
localStorage.setItem('profile_data', JSON.stringify(profile));
localStorage.setItem('app_version', APP_VERSION);

// Очистка при обновлении версии
function checkAndClearOldCache() {
  const storedVersion = localStorage.getItem('app_version');
  if (storedVersion !== APP_VERSION) {
    localStorage.clear();
    localStorage.setItem('app_version', APP_VERSION);
  }
}
```

### 3. Image Optimization

```javascript
// Загрузка фото через Media Service
// - Сжатие JPEG/WebP
// - Генерация thumbnails
// - CDN delivery
```

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Открыть в браузере для разработки
open webapp/index.html

# 2. Использовать Telegram WebApp тестер
# https://webappbot.web.app/

# 3. Тестировать в реальном боте
# @BotFather -> /newapp
```

### Browser DevTools

```javascript
// Debug режим
console.log('Telegram WebApp:', tg);
console.log('Platform:', tg.platform);
console.log('Theme:', tg.colorScheme);
console.log('Init Data:', tg.initDataUnsafe);
```

---

## 📚 Best Practices

### 1. User Experience

✅ **DO:**
- Использовать MainButton вместо обычных кнопок
- Добавлять Haptic Feedback на все действия
- Адаптироваться к теме Telegram
- Показывать BackButton где нужно
- Использовать native alerts/confirms

❌ **DON'T:**
- Не блокировать UI долгими операциями
- Не использовать custom модальные окна
- Не игнорировать Safe Areas
- Не забывать про тактильную обратную связь

### 2. Performance

✅ **DO:**
- Lazy load данных порционно
- Кэшировать в localStorage
- Оптимизировать изображения
- Использовать CSS transitions

❌ **DON'T:**
- Не загружать всё сразу
- Не хранить большие объемы в памяти
- Не делать синхронные операции

### 3. Security

✅ **DO:**
- Всегда валидировать Telegram data на бэкенде
- Использовать JWT для аутентификации
- Отправлять токены в Headers
- Обновлять токены при 401

❌ **DON'T:**
- Не доверять client-side данным
- Не хранить секреты в коде
- Не отправлять пароли

---

## 🔄 Deployment

### 1. Build для Production

```bash
# Минификация JavaScript
npx terser webapp/js/app.js -c -m -o webapp/js/app.min.js

# Минификация CSS
npx csso webapp/css/style.css -o webapp/css/style.min.css

# Обновить HTML для использования минифицированных файлов
```

### 2. Hosting

```bash
# Статические файлы через Nginx
# Dockerfile для webapp
FROM nginx:alpine
COPY webapp/ /usr/share/nginx/html/
EXPOSE 80
```

### 3. HTTPS Setup

```yaml
# docker-compose.yml с Traefik
traefik:
  labels:
    - "traefik.http.routers.webapp.rule=Host(`app.example.com`)"
    - "traefik.http.routers.webapp.tls.certresolver=letsencrypt"
```

---

## 📖 Resources

### Official Documentation

- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [WebApp Demo Bot](https://t.me/DurgerKingBot)

### Useful Tools

- [Telegram WebApp Validator](https://webappbot.web.app/)
- [ngrok](https://ngrok.com/) - Local HTTPS tunnel for testing
- [BotFather](https://t.me/BotFather) - Create and manage bots

### Community

- [Telegram Bot Developers](https://t.me/BotDevelopment)
- [WebApp Developers Chat](https://t.me/WebAppDevs)

---

## 🐛 Troubleshooting

### Issue: WebApp не открывается

```javascript
// Проверить консоль браузера
console.log('Telegram SDK loaded:', !!window.Telegram);
console.log('WebApp available:', !!window.Telegram?.WebApp);
```

**Решение:**
- Убедиться что SDK загружен: `<script src="https://telegram.org/js/telegram-web-app.js"></script>`
- Проверить что страница открыта в Telegram

### Issue: Theme не применяется

```javascript
// Проверить theme params
console.log('Theme params:', tg.themeParams);
console.log('Color scheme:', tg.colorScheme);
```

**Решение:**
- Убедиться что `applyTheme()` вызывается после инициализации
- Проверить CSS переменные в DevTools

### Issue: MainButton не работает

```javascript
// Проверить состояние кнопки
console.log('MainButton visible:', tg.MainButton.isVisible);
console.log('MainButton enabled:', tg.MainButton.isActive);
```

**Решение:**
- Вызвать `tg.MainButton.show()` и `tg.MainButton.enable()`
- Удалить старые обработчики: `tg.MainButton.offClick(oldHandler)`

---

## 🎯 Roadmap

### Planned Features

- [ ] **Offline Support** - Service Workers для offline режима
- [ ] **Push Notifications** - Через Telegram Bot API
- [ ] **Deep Linking** - Прямые ссылки на профили
- [ ] **Animations** - Smooth transitions между экранами
- [ ] **PWA Manifest** - Install as app
- [ ] **WebRTC** - Video/Audio звонки
- [ ] **Stories** - Instagram-like stories

### Improvements

- [ ] **Code Splitting** - Разделение JS по экранам
- [ ] **TypeScript** - Типизация кода
- [ ] **State Management** - Redux/MobX
- [ ] **Unit Tests** - Jest для компонентов
- [ ] **E2E Tests** - Playwright для UI

---

**Last Updated:** 2025-01-06  
**Version:** 1.3.0  
**Author:** Dating Development Team
