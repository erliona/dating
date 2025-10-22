#!/bin/bash

echo "🔍 ПРОВЕРКА DASHBOARDS GRAFANA"
echo "============================="

# Проверяем доступность Grafana
echo ""
echo "📊 СТАТУС GRAFANA:"
echo "------------------"
ssh root@dating.serge.cc "curl -s http://localhost:3000/api/health"

echo ""
echo "📈 ИСТОЧНИКИ ДАННЫХ:"
echo "--------------------"
ssh root@dating.serge.cc "curl -s -u admin:admin 'http://localhost:3000/api/datasources' | jq '.[] | {name: .name, type: .type, url: .url}'"

echo ""
echo "📋 DASHBOARDS:"
echo "--------------"
DASHBOARDS=$(ssh root@dating.serge.cc "curl -s -u admin:admin 'http://localhost:3000/api/search?type=dash-db' | jq -r '.[] | .title'")
echo "Всего дашбордов: $(echo "$DASHBOARDS" | wc -l)"
echo "$DASHBOARDS"

echo ""
echo "🔍 ПРОВЕРКА МЕТРИК:"
echo "-------------------"

# Проверяем HTTP метрики
echo "HTTP метрики:"
ssh root@dating.serge.cc "curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' | jq '.data.result | length'"

# Проверяем бизнес-метрики
echo "Бизнес-метрики:"
ssh root@dating.serge.cc "curl -s 'http://localhost:9090/api/v1/query?query=users_total' | jq '.data.result | length'"

echo ""
echo "📝 ПРОВЕРКА ЛОГОВ:"
echo "------------------"

# Проверяем логи в Loki
echo "Логи в Loki:"
ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/query?query=%7Bcontainer_name%3D%22dating-microservices-api-gateway-1%22%7D&limit=1' | jq '.data.result | length'"

echo ""
echo "🎯 РЕКОМЕНДАЦИИ:"
echo "================"
echo "1. Проверить, что все дашборды используют правильные источники данных"
echo "2. Убедиться, что метрики отображаются корректно"
echo "3. Проверить, что логи интегрированы в дашборды"
echo "4. Убедиться, что бизнес-метрики генерируются"
