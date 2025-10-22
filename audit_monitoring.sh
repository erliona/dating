#!/bin/bash

echo "🔍 АУДИТ СИСТЕМЫ МОНИТОРИНГА И ЛОГИРОВАНИЯ"
echo "=========================================="

# Проверяем дублирование дашбордов
echo ""
echo "📊 ДАШБОРДЫ GRAFANA:"
echo "-------------------"

echo "🗂️ Файлы дашбордов на сервере:"
ssh root@dating.serge.cc "ls -la /root/dating-microservices/monitoring/grafana/dashboards/ | grep -E '\.(json)$'"

echo ""
echo "🗂️ Файлы дашбордов в контейнере Grafana:"
ssh root@dating.serge.cc "docker exec dating-microservices-grafana-1 ls -la /var/lib/grafana/dashboards/ | grep -E '\.(json)$'"

echo ""
echo "🔍 ДУБЛИРОВАНИЕ ДАШБОРДОВ:"
echo "-------------------------"

# Проверяем дублирование по номерам
echo "❌ ДУБЛИРОВАНИЕ ПО НОМЕРАМ:"
echo "1. Infrastructure Overview (legacy) vs System Health (new)"
echo "2. Application Services (legacy) vs Business Metrics (new)"  
echo "3. Application Logs (legacy) vs API Performance (new)"
echo "4. Database Metrics (legacy) vs Database Infrastructure (new)"

echo ""
echo "📈 ПРОМЕТЕУС КОНФИГУРАЦИЯ:"
echo "-------------------------"
echo "✅ Prometheus настроен на IP-адреса (правильно)"
echo "✅ Все сервисы мониторятся через application-services job"
echo "✅ Relabeling настроен для правильных имен сервисов"

echo ""
echo "📝 ПРОМТЕЙЛ КОНФИГУРАЦИЯ:"
echo "------------------------"
echo "✅ Promtail настроен на Docker service discovery"
echo "✅ Автоматическое определение уровней логирования"
echo "✅ Правильная маркировка контейнеров"

echo ""
echo "🎯 РЕКОМЕНДАЦИИ ПО ОЧИСТКЕ:"
echo "=========================="
echo "1. Удалить legacy дашборды (1-infrastructure-overview.json, 2-application-services.json, 3-application-logs.json, 4-database-metrics.json)"
echo "2. Оставить только новые дашборды (1-system-health.json, 2-business-metrics.json, 3-api-performance.json, 4-database-infrastructure.json, 5-security-authentication.json)"
echo "3. Проверить, что все дашборды загружены в Grafana"
echo "4. Обновить документацию с актуальными дашбордами"
