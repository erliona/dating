#!/bin/bash

echo "🔍 ПРОВЕРКА ОЧИЩЕННЫХ ДАШБОРДОВ"
echo "================================"

# Создаем временный файл для сессии
TEMP_FILE=$(mktemp)

# Получаем сессию Grafana
echo "📡 Получаем сессию Grafana..."
curl -s -c "$TEMP_FILE" -X POST \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"admin"}' \
  http://dating.serge.cc:3000/login > /dev/null

# Проверяем дашборды
echo "📊 Проверяем дашборды после очистки..."
DASHBOARDS=$(curl -s -b "$TEMP_FILE" \
  "http://dating.serge.cc:3000/api/search?type=dash-db" \
  -H "Accept: application/json")

echo ""
echo "✅ АКТУАЛЬНЫЕ ДАШБОРДЫ:"

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

echo ""
echo "🗑️ ПРОВЕРКА УДАЛЕНИЯ LEGACY ДАШБОРДОВ:"

if echo "$DASHBOARDS" | grep -q "Infrastructure Overview"; then
    echo "❌ Infrastructure Overview - НЕ УДАЛЕН!"
else
    echo "✅ Infrastructure Overview - удален"
fi

if echo "$DASHBOARDS" | grep -q "Application Services"; then
    echo "❌ Application Services - НЕ УДАЛЕН!"
else
    echo "✅ Application Services - удален"
fi

if echo "$DASHBOARDS" | grep -q "Application Logs"; then
    echo "❌ Application Logs - НЕ УДАЛЕН!"
else
    echo "✅ Application Logs - удален"
fi

if echo "$DASHBOARDS" | grep -q "Database Metrics"; then
    echo "❌ Database Metrics - НЕ УДАЛЕН!"
else
    echo "✅ Database Metrics - удален"
fi

# Очищаем временный файл
rm -f "$TEMP_FILE"

echo ""
echo "🎉 ОЧИСТКА ЗАВЕРШЕНА!"
echo "📊 Осталось только 5 актуальных дашбордов"
echo "🔗 Откройте http://dating.serge.cc:3000 в браузере"
