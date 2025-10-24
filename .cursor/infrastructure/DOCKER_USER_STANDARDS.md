# Docker User Standards

## 🎯 **Единые правила пользователей для всех Docker контейнеров**

### 📋 **СТАНДАРТЫ ПОЛЬЗОВАТЕЛЕЙ**

#### **1. Python Services (Все микросервисы)**
```dockerfile
# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка прав
RUN chown -R appuser:appuser /app

# Переключение на пользователя
USER appuser
```

#### **2. Database Services (PostgreSQL)**
```dockerfile
# PostgreSQL использует встроенного пользователя postgres
# НЕ создаем дополнительных пользователей
# PostgreSQL сам управляет пользователями
```

#### **3. Web Services (Nginx)**
```dockerfile
# Nginx использует встроенного пользователя nginx
# НЕ создаем дополнительных пользователей
# Nginx сам управляет пользователями
```

#### **4. Monitoring Services (Prometheus, Grafana, etc.)**
```dockerfile
# Используем встроенных пользователей
# Prometheus: nobody
# Grafana: grafana
# НЕ создаем дополнительных пользователей
```

### 🔧 **РЕАЛИЗАЦИЯ ПО СЕРВИСАМ**

#### **Python Services (appuser)**
- ✅ `telegram-bot` - USER appuser
- ✅ `auth-service` - USER appuser  
- ✅ `profile-service` - USER appuser
- ✅ `discovery-service` - USER appuser
- ✅ `media-service` - USER appuser
- ✅ `chat-service` - USER appuser
- ✅ `notification-service` - USER appuser
- ✅ `data-service` - USER appuser
- ✅ `admin-service` - USER appuser (закомментирован)
- ✅ `api-gateway` - USER appuser

#### **Web Services (nginx)**
- ❌ `webapp` - ПРОБЛЕМА: пытается использовать nginx user
- 🔧 **РЕШЕНИЕ**: Запускать от root с `user root;` в nginx.conf

#### **Database Services (postgres)**
- ✅ `db` - Встроенный пользователь postgres

#### **Message Queue (rabbitmq)**
- ✅ `rabbitmq` - Встроенный пользователь rabbitmq

#### **Monitoring Services**
- ✅ `prometheus` - Встроенный пользователь nobody
- ✅ `grafana` - Встроенный пользователь grafana
- ✅ `loki` - Встроенный пользователь nobody
- ✅ `promtail` - Встроенный пользователь nobody
- ✅ `cadvisor` - Встроенный пользователь root
- ✅ `node-exporter` - Встроенный пользователь nobody
- ✅ `postgres-exporter` - Встроенный пользователь nobody

### 🚨 **ПРОБЛЕМЫ И РЕШЕНИЯ**

#### **Проблема 1: Webapp Nginx**
```
ERROR: setgid(101) failed (1: Operation not permitted)
```
**Причина**: Nginx пытается запустить worker процессы от пользователя nginx (ID 101), но security restrictions не позволяют.

**Решение**: 
```nginx
user root;
worker_processes auto;
```

#### **Проблема 2: Security Restrictions**
```
cap_drop: [ALL] + no-new-privileges:true
```
**Причина**: Слишком строгие ограничения безопасности.

**Решение**: Добавить необходимые capabilities:
```yaml
cap_add:
  - CHOWN
  - FOWNER
  - SETGID  # Для Nginx
  - SETUID  # Для некоторых сервисов
```

### 📝 **ПРАВИЛА РАЗРАБОТКИ**

#### **1. Python Services**
- ВСЕГДА создавать пользователя `appuser`
- ВСЕГДА переключаться на `USER appuser`
- ВСЕГДА устанавливать права `chown -R appuser:appuser /app`

#### **2. Web Services (Nginx)**
- ВСЕГДА использовать `user root;` в nginx.conf
- НЕ создавать дополнительных пользователей
- НЕ переключаться на USER в Dockerfile

#### **3. Database Services**
- НЕ создавать дополнительных пользователей
- Использовать встроенных пользователей
- НЕ переключаться на USER в Dockerfile

#### **4. Monitoring Services**
- НЕ создавать дополнительных пользователей
- Использовать встроенных пользователей
- НЕ переключаться на USER в Dockerfile

### 🔍 **ПРОВЕРКА СООТВЕТСТВИЯ**

#### **Команды для проверки:**
```bash
# Проверить пользователя в контейнере
docker compose exec <service> whoami

# Проверить процессы
docker compose exec <service> ps aux

# Проверить права на файлы
docker compose exec <service> ls -la /app
```

#### **Ожидаемые результаты:**
- Python services: `appuser`
- Web services: `root` (для Nginx)
- Database services: `postgres`
- Monitoring services: соответствующие встроенные пользователи

### 📊 **СТАТУС СООТВЕТСТВИЯ**

| Service | Expected User | Current Status | Action Needed |
|---------|---------------|----------------|---------------|
| telegram-bot | appuser | ✅ | - |
| auth-service | appuser | ✅ | - |
| profile-service | appuser | ✅ | - |
| discovery-service | appuser | ✅ | - |
| media-service | appuser | ✅ | - |
| chat-service | appuser | ✅ | - |
| notification-service | appuser | ✅ | - |
| data-service | appuser | ✅ | - |
| admin-service | appuser | ✅ | - |
| api-gateway | appuser | ✅ | - |
| webapp | root | ✅ | Fixed nginx.conf |
| db | postgres | ✅ | - |
| rabbitmq | rabbitmq | ✅ | - |
| prometheus | nobody | ✅ | - |
| grafana | grafana | ✅ | - |
| loki | nobody | ✅ | - |
| promtail | nobody | ✅ | - |
| cadvisor | root | ✅ | - |
| node-exporter | nobody | ✅ | - |
| postgres-exporter | nobody | ✅ | - |

### 🎯 **ПЛАН ДЕЙСТВИЙ**

1. ✅ **Python Services** - уже соответствуют стандарту
2. 🔧 **Webapp** - исправить nginx.conf (уже сделано)
3. ✅ **Database Services** - уже соответствуют стандарту  
4. ✅ **Monitoring Services** - уже соответствуют стандарту
5. 📝 **Документировать** - создать этот документ
6. 🔍 **Проверить** - убедиться, что все работает

### 🚀 **РЕЗУЛЬТАТ**

После применения этих стандартов:
- Все Python сервисы работают от `appuser`
- Webapp работает от `root` (требование Nginx)
- Database и Monitoring сервисы используют встроенных пользователей
- Единообразие и предсказуемость во всех контейнерах
- Безопасность и стабильность системы
