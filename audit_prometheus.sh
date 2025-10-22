#!/bin/bash

echo "🔍 АУДИТ PROMETHEUS НА ДУБЛИРОВАНИЕ"
echo "===================================="

# Проверяем конфигурацию Prometheus
echo ""
echo "📊 КОНФИГУРАЦИЯ PROMETHEUS:"
echo "---------------------------"

echo "✅ Jobs в конфигурации:"
ssh root@dating.serge.cc "grep -A 1 'job_name:' /root/dating-microservices/monitoring/prometheus/prometheus.yml | grep 'job_name:' | sed 's/.*job_name: //' | sed 's/'\''//g'"

echo ""
echo "📈 АКТИВНЫЕ TARGETS:"
echo "--------------------"
ssh root@dating.serge.cc "curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, instance: .labels.instance, health: .health}'"

echo ""
echo "🔍 ПРОВЕРКА ДУБЛИРОВАНИЯ INSTANCE'ОВ:"
echo "-------------------------------------"

# Получаем все instance'ы
INSTANCES=$(ssh root@dating.serge.cc "curl -s 'http://localhost:9090/api/v1/label/instance/values' | jq -r '.data[]'")

echo "Все instance'ы:"
echo "$INSTANCES"

echo ""
echo "🔍 АНАЛИЗ ДУБЛИРОВАНИЯ:"

# Проверяем дублирование по сервисам
echo ""
echo "❌ ПОТЕНЦИАЛЬНОЕ ДУБЛИРОВАНИЕ:"

# API Gateway
if echo "$INSTANCES" | grep -q "172.18.0.8:8080" && echo "$INSTANCES" | grep -q "api-gateway:8080"; then
    echo "❌ API Gateway: 172.18.0.8:8080 vs api-gateway:8080"
else
    echo "✅ API Gateway: только IP-адрес"
fi

# Auth Service
if echo "$INSTANCES" | grep -q "172.18.0.12:8081" && echo "$INSTANCES" | grep -q "auth-service:8081"; then
    echo "❌ Auth Service: 172.18.0.12:8081 vs auth-service:8081"
else
    echo "✅ Auth Service: только IP-адрес"
fi

# Profile Service
if echo "$INSTANCES" | grep -q "172.18.0.13:8082" && echo "$INSTANCES" | grep -q "profile-service:8082"; then
    echo "❌ Profile Service: 172.18.0.13:8082 vs profile-service:8082"
else
    echo "✅ Profile Service: только IP-адрес"
fi

# Discovery Service
if echo "$INSTANCES" | grep -q "172.18.0.14:8083" && echo "$INSTANCES" | grep -q "discovery-service:8083"; then
    echo "❌ Discovery Service: 172.18.0.14:8083 vs discovery-service:8083"
else
    echo "✅ Discovery Service: только IP-адрес"
fi

# Media Service
if echo "$INSTANCES" | grep -q "172.18.0.15:8084" && echo "$INSTANCES" | grep -q "media-service:8084"; then
    echo "❌ Media Service: 172.18.0.15:8084 vs media-service:8084"
else
    echo "✅ Media Service: только IP-адрес"
fi

# Chat Service
if echo "$INSTANCES" | grep -q "172.18.0.16:8085" && echo "$INSTANCES" | grep -q "chat-service:8085"; then
    echo "❌ Chat Service: 172.18.0.16:8085 vs chat-service:8085"
else
    echo "✅ Chat Service: только IP-адрес"
fi

# Admin Service
if echo "$INSTANCES" | grep -q "172.18.0.9:8086" && echo "$INSTANCES" | grep -q "admin-service:8086"; then
    echo "❌ Admin Service: 172.18.0.9:8086 vs admin-service:8086"
else
    echo "✅ Admin Service: только IP-адрес"
fi

echo ""
echo "📊 СТАТИСТИКА МЕТРИК:"
echo "--------------------"
TOTAL_METRICS=$(ssh root@dating.serge.cc "curl -s 'http://localhost:9090/api/v1/label/__name__/values' | jq '.data | length'")
echo "Всего уникальных метрик: $TOTAL_METRICS"

TOTAL_INSTANCES=$(ssh root@dating.serge.cc "curl -s 'http://localhost:9090/api/v1/label/instance/values' | jq '.data | length'")
echo "Всего instance'ов: $TOTAL_INSTANCES"

echo ""
echo "🎯 РЕКОМЕНДАЦИИ:"
echo "================"
echo "1. Если есть дублирование instance'ов - очистить старые метрики"
echo "2. Проверить, что все сервисы используют IP-адреса"
echo "3. Убедиться, что нет старых конфигураций"
echo "4. При необходимости перезапустить Prometheus для очистки кэша"
