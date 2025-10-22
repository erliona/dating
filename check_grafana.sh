#!/bin/bash

# Проверка доступности Grafana и настройка
echo "🔍 Проверяем доступность Grafana..."

# Проверяем, что Grafana отвечает
if curl -s http://dating.serge.cc:3000/api/health > /dev/null; then
    echo "✅ Grafana доступна по адресу: http://dating.serge.cc:3000"
else
    echo "❌ Grafana недоступна"
    exit 1
fi

# Проверяем, что Prometheus доступен
if curl -s http://dating.serge.cc:9090/api/v1/status/config > /dev/null; then
    echo "✅ Prometheus доступен по адресу: http://dating.serge.cc:9090"
else
    echo "❌ Prometheus недоступен"
    exit 1
fi

echo ""
echo "📊 Доступные дашборды:"
echo "1. Infrastructure Overview - обзор инфраструктуры"
echo "2. Application Services - метрики приложений"
echo "3. Application Logs - логи приложений"
echo "4. Database Metrics - метрики базы данных"

echo ""
echo "🔗 Ссылки для доступа:"
echo "• Grafana: http://dating.serge.cc:3000"
echo "• Prometheus: http://dating.serge.cc:9090"
echo "• Webapp: http://dating.serge.cc"
echo "• Admin Panel: http://dating.serge.cc/admin"

echo ""
echo "👤 Для входа в Grafana используйте:"
echo "• Логин: admin"
echo "• Пароль: admin (по умолчанию)"
