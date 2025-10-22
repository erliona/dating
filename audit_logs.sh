#!/bin/bash

echo "🔍 АУДИТ СИСТЕМЫ ЛОГИРОВАНИЯ"
echo "============================="

# Проверяем статус Loki
echo ""
echo "📊 СТАТУС LOKI:"
echo "---------------"
ssh root@dating.serge.cc "curl -s http://localhost:3100/ready"

echo ""
echo "📊 СТАТУС ПРОМТЕЙЛ:"
echo "------------------"
ssh root@dating.serge.cc "docker logs dating-microservices-promtail-1 --tail 5 | grep -E '(added Docker target|finished transferring)' | wc -l"

echo ""
echo "📈 КОНТЕЙНЕРЫ В LOKI:"
echo "---------------------"
CONTAINERS=$(ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/label/container_name/values' | jq -r '.data[]'")
echo "Всего контейнеров: $(echo "$CONTAINERS" | wc -l)"
echo "$CONTAINERS"

echo ""
echo "🔍 АНАЛИЗ ДУБЛИРОВАНИЯ:"
echo "-----------------------"

# Проверяем, есть ли дублирование по именам контейнеров
echo "❌ ПОТЕНЦИАЛЬНОЕ ДУБЛИРОВАНИЕ:"

# Проверяем дублирование по сервисам
SERVICES=$(ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/label/service/values' | jq -r '.data[]' 2>/dev/null || echo 'No service label'")
echo "Сервисы: $SERVICES"

# Проверяем дублирование по job'ам
JOBS=$(ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/label/job/values' | jq -r '.data[]'")
echo "Jobs: $JOBS"

echo ""
echo "📊 СТАТИСТИКА ЛОГОВ:"
echo "--------------------"

# Проверяем общее количество логов
TOTAL_LOGS=$(ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/query?query={job=\"docker\"}&limit=1' | jq '.data.result | length'")
echo "Всего логов от Docker: $TOTAL_LOGS"

# Проверяем логи по уровням
echo ""
echo "📝 УРОВНИ ЛОГИРОВАНИЯ:"
LEVELS=$(ssh root@dating.serge.cc "curl -s 'http://localhost:3100/loki/api/v1/label/level/values' | jq -r '.data[]' 2>/dev/null || echo 'No level labels'")
echo "Уровни: $LEVELS"

echo ""
echo "🎯 РЕКОМЕНДАЦИИ:"
echo "================"
echo "1. Проверить, что все сервисы логируются корректно"
echo "2. Убедиться, что нет дублирования логов"
echo "3. Проверить структуру логов (JSON vs plain text)"
echo "4. Убедиться, что уровни логирования определяются правильно"
