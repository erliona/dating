# 🚀 Mini App Quick Start Guide

Быстрый старт для разработки Dating Mini App.

---

## 📋 Предварительные требования

- Telegram аккаунт
- Telegram Bot (создать у [@BotFather](https://t.me/BotFather))
- Редактор кода (VS Code рекомендуется)
- Базовые знания HTML/CSS/JavaScript

---

## 🎯 5-минутный старт

### 1. Создать Mini App в BotFather

```
/newapp
<выберите вашего бота>
<название: Dating App>
<описание: Dating Mini App>
<фото приложения: опционально>
<URL: https://your-domain.com/webapp/>
```

### 2. Открыть webapp файлы

```bash
cd webapp/
# Структура:
# - index.html  (основной файл)
# - js/app.js   (логика приложения)
# - css/style.css (стили)
```

### 3. Тестировать локально

**Вариант А: Python HTTP сервер**
```bash
cd webapp/
python3 -m http.server 8000
# Открыть: http://localhost:8000
```

**Вариант Б: Live Server (VS Code)**
1. Установить расширение "Live Server"
2. Правый клик на `index.html` → "Open with Live Server"

**Вариант В: ngrok для тестирования в Telegram**
```bash
# Запустить локальный сервер
python3 -m http.server 8000

# В другом терминале
ngrok http 8000
# Копировать HTTPS URL (например: https://abc123.ngrok.io)
# Обновить URL в BotFather: /setmenubutton -> Web App URL
```

### 4. Открыть в Telegram

- Найти своего бота в Telegram
- Нажать кнопку Menu → "Dating App"
- Mini App откроется!

---

## 🧩 Основные компоненты

### Telegram WebApp SDK

Всегда загружается первым в `index.html`:

```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
```

### Инициализация

```javascript
// app.js
const tg = window.Telegram.WebApp;
tg.expand();  // Полноэкранный режим
tg.ready();   // Уведомить Telegram что приложение готово
```

### Основные API

```javascript
// MainButton
tg.MainButton.setText('Создать профиль');
tg.MainButton.show();
tg.MainButton.onClick(handleSubmit);

// BackButton
tg.BackButton.show();
tg.BackButton.onClick(handleBack);

// Haptic Feedback
tg.HapticFeedback.impactOccurred('medium');
tg.HapticFeedback.notificationOccurred('success');

// Theme
const bgColor = tg.themeParams.bg_color;
const textColor = tg.themeParams.text_color;

// User Info
const userId = tg.initDataUnsafe.user.id;
const userName = tg.initDataUnsafe.user.first_name;
```

---

## 🎨 Стилизация под Telegram

### CSS Variables

Автоматически синхронизируются с темой Telegram:

```css
:root {
  --tg-theme-bg-color: #ffffff;
  --tg-theme-text-color: #000000;
  --tg-theme-button-color: #2481cc;
  /* и другие... */
}

.card {
  background: var(--tg-theme-bg-color);
  color: var(--tg-theme-text-color);
}
```

### Применение темы

```javascript
function applyTheme() {
  const root = document.documentElement;
  for (const [key, cssVar] of Object.entries(themeMap)) {
    root.style.setProperty(cssVar, tg.themeParams[key]);
  }
}

// Слушатель изменения темы
tg.onEvent('themeChanged', applyTheme);
```

---

## 🔌 Интеграция с Backend

### API Gateway

```javascript
const API_BASE_URL = 'http://localhost:8080';

// Получить JWT токен
async function getAuthToken() {
  const response = await fetch(`${API_BASE_URL}/auth/telegram`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: tg.initData })
  });
  return (await response.json()).access_token;
}

// Использовать токен
const response = await fetch(`${API_BASE_URL}/api/profile`, {
  headers: { 'Authorization': `Bearer ${authToken}` }
});
```

### Микросервисы

| Сервис | Порт | Эндпоинт |
|--------|------|----------|
| Auth | 8081 | `/auth/*` |
| Profile | 8082 | `/profiles/*` |
| Discovery | 8083 | `/discovery/*` |
| Media | 8084 | `/media/*` |
| Chat | 8085 | `/chat/*` |

---

## 🛠️ Разработка

### Структура проекта

```
webapp/
├── index.html           # Главная страница
├── css/
│   └── style.css       # Стили
└── js/
    ├── app.js          # Основная логика
    ├── discovery.js    # Поиск и свайпы
    └── navigation.js   # Навигация
```

### Добавить новый экран

1. **Добавить HTML в `index.html`:**

```html
<div id="new-screen" class="container hidden">
  <h2>Новый экран</h2>
  <p>Контент...</p>
</div>
```

2. **Добавить функцию показа в `navigation.js`:**

```javascript
function showNewScreen() {
  hideAllScreens();
  document.getElementById('new-screen').classList.remove('hidden');
  showBottomNav();
  setActiveTab('new');
  
  // Настроить MainButton
  if (tg && tg.MainButton) {
    tg.MainButton.setText('Действие');
    tg.MainButton.show();
    tg.MainButton.onClick(handleNewScreenAction);
  }
}
```

3. **Добавить в навигацию:**

```html
<button class="nav-item" onclick="showNewScreen()" data-tab="new">
  <svg>...</svg>
  <span>Новое</span>
</button>
```

### Добавить API вызов

```javascript
async function loadData() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/data`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    if (tg) tg.showAlert('Ошибка загрузки данных');
    return null;
  }
}
```

---

## 🐛 Отладка

### Console Logs

```javascript
console.log('Telegram WebApp:', tg);
console.log('User:', tg.initDataUnsafe.user);
console.log('Theme:', tg.colorScheme);
console.log('Platform:', tg.platform);
```

### Telegram Web Inspector

1. Открыть Mini App в Desktop Telegram
2. Правый клик → "Inspect Element"
3. Использовать DevTools как обычно

### Common Issues

**Проблема: WebApp не загружается**
```javascript
// Проверить что SDK загружен
if (!window.Telegram || !window.Telegram.WebApp) {
  console.error('Telegram WebApp SDK not loaded');
}
```

**Проблема: MainButton не показывается**
```javascript
// Убедиться что вызваны show() и enable()
tg.MainButton.show();
tg.MainButton.enable();

// Проверить состояние
console.log('Visible:', tg.MainButton.isVisible);
console.log('Active:', tg.MainButton.isActive);
```

**Проблема: Тема не применяется**
```javascript
// Проверить что applyTheme() вызван после инициализации
setTimeout(applyTheme, 100);

// Или дождаться события ready
tg.onEvent('ready', applyTheme);
```

---

## 📦 Деплой

### Production Checklist

- [ ] Минифицировать JS/CSS
- [ ] Оптимизировать изображения
- [ ] Настроить HTTPS (обязательно!)
- [ ] Обновить API_BASE_URL на production URL
- [ ] Обновить Web App URL в BotFather
- [ ] Протестировать в iOS/Android Telegram

### Build

```bash
# Минификация JavaScript
npx terser webapp/js/app.js -c -m -o webapp/js/app.min.js

# Минификация CSS
npx csso webapp/css/style.css -o webapp/css/style.min.css
```

### HTTPS

```bash
# Использовать Let's Encrypt через Traefik
# см. docker-compose.yml
```

---

## 📚 Дополнительные ресурсы

- [Telegram WebApp API Docs](https://core.telegram.org/bots/webapps)
- [Mini App Architecture](./MINIAPP_ARCHITECTURE.md)
- [Monitoring Setup](./MONITORING_SETUP.md)
- [Port Mapping](./PORT_MAPPING.md)

---

## 💡 Tips & Tricks

### Haptic Feedback везде

```javascript
// Кнопки
button.onclick = () => {
  tg.HapticFeedback.impactOccurred('medium');
  // ...
};

// Успех
tg.HapticFeedback.notificationOccurred('success');

// Ошибка
tg.HapticFeedback.notificationOccurred('error');
```

### Responsive для всех устройств

```css
/* Safe Areas для iPhone X+ */
.container {
  padding-bottom: max(16px, env(safe-area-inset-bottom));
}

/* Учитывать высоту viewport */
.full-screen {
  height: calc(var(--tg-viewport-height, 100vh) - 64px);
}
```

### Кэширование данных

```javascript
// Сохранить
localStorage.setItem('profile', JSON.stringify(profile));

// Загрузить
const profile = JSON.parse(localStorage.getItem('profile'));

// Очистить при обновлении версии
if (localStorage.getItem('app_version') !== APP_VERSION) {
  localStorage.clear();
  localStorage.setItem('app_version', APP_VERSION);
}
```

---

## 🎓 Следующие шаги

1. ✅ Прочитать [Mini App Architecture](./MINIAPP_ARCHITECTURE.md)
2. 🔍 Изучить существующий код в `webapp/js/`
3. 🎨 Настроить дизайн под свои нужды
4. 🔌 Подключить к своему backend
5. 📱 Протестировать на реальных устройствах
6. 🚀 Задеплоить на production

---

**Happy coding! 🎉**

*Если возникли вопросы, создайте Issue на GitHub*
