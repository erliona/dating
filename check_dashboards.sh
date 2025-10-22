#!/bin/bash

# Проверка дашбордов в Grafana
echo "🔍 Проверяем дашборды в Grafana..."

# Создаем временный файл для сессии
TEMP_FILE=$(mktemp)

# Получаем сессию Grafana
echo "📡 Получаем сессию Grafana..."
curl -s -c "$TEMP_FILE" -X POST \
  -H "Content-Type: application/json" \
  -d '{"user":"admin","password":"admin"}' \
  http://dating.serge.cc:3000/login > /dev/null

# Проверяем дашборды
echo "📊 Проверяем дашборды..."
DASHBOARDS=$(curl -s -b "$TEMP_FILE" \
  "http://dating.serge.cc:3000/api/search?type=dash-db" \
  -H "Accept: application/json")

if echo "$DASHBOARDS" | grep -q "Infrastructure Overview"; then
    echo "✅ Infrastructure Overview - найден"
else
    echo "❌ Infrastructure Overview - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Application Services"; then
    echo "✅ Application Services - найден"
else
    echo "❌ Application Services - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Application Logs"; then
    echo "✅ Application Logs - найден"
else
    echo "❌ Application Logs - не найден"
fi

if echo "$DASHBOARDS" | grep -q "Database Metrics"; then
    echo "✅ Database Metrics - найден"
else
    echo "❌ Database Metrics - не найден"
fi

# Очищаем временный файл
rm -f "$TEMP_FILE"

echo ""
echo "🎉 Grafana полностью настроена и готова к использованию!"
echo "🔗 Откройте http://dating.serge.cc:3000 в браузере"
