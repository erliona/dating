#!/bin/bash

# Проверка новых дашбордов в Grafana
echo "🔍 Проверяем новые дашборды в Grafana..."

# Создаем временный файл для сессии
TEMP_FILE=$(mktemp)

# Получаем сессию Grafana
echo "📡 Получаем сессию Grafana..."
curl -s -c "$TEMP_FILE" -X POST \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"admin"}' \
  http://dating.serge.cc:3000/login > /dev/null

# Проверяем дашборды
echo "📊 Проверяем новые дашборды..."
DASHBOARDS=$(curl -s -b "$TEMP_FILE" \
  "http://dating.serge.cc:3000/api/search?type=dash-db" \
  -H "Accept: application/json")

echo "🎯 Новые дашборды:"

if echo "$DASHBOARDS" | grep -q "System Health Dashboard"; then
    echo "✅ System Health Dashboard - найден"
else
    echo "❌ System Health Dashboard - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Dating App Business Metrics"; then
    echo "✅ Dating App Business Metrics - найден"
else
    echo "❌ Dating App Business Metrics - не найден"
fi

if echo "$DASHBOARDS" | grep -q "API Performance Dashboard"; then
    echo "✅ API Performance Dashboard - найден"
else
    echo "❌ API Performance Dashboard - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Database & Infrastructure"; then
    echo "✅ Database & Infrastructure - найден"
else
    echo "❌ Database & Infrastructure - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Security & Authentication"; then
    echo "✅ Security & Authentication - найден"
else
    echo "❌ Security & Authentication - не найден"
fi

# Очищаем временный файл
rm -f "$TEMP_FILE"

echo ""
echo "🎉 Новые дашборды загружены!"
echo "🔗 Откройте http://dating.serge.cc:3000 в браузере"
echo ""
echo "📊 Доступные дашборды:"
echo "1. System Health Dashboard - общее состояние системы"
echo "2. Dating App Business Metrics - бизнес-метрики приложения"
echo "3. API Performance Dashboard - производительность API"
echo "4. Database & Infrastructure - база данных и инфраструктура"
echo "5. Security & Authentication - безопасность и аутентификация"
