# Routing Strategy Documentation

## Overview

This document outlines the comprehensive routing strategy for the Dating Platform, including API Gateway routing, Traefik configuration, service discovery, and load balancing.

## Architecture Overview

### Routing Layers
1. **Traefik (Reverse Proxy)**: External traffic routing and SSL termination
2. **API Gateway**: Internal service routing and request processing
3. **Service Mesh**: Inter-service communication and load balancing
4. **Database Routing**: Connection pooling and failover

## Traefik Configuration

### Production Routing
```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - --api.dashboard=true
      - --api.insecure=false
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
      - --certificatesresolvers.letsencrypt.acme.email=admin@dating.serge.cc
      - --certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.dating.serge.cc`)"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
```

### Route Priority Matrix
| Priority | Route | Description | Middleware |
|----------|-------|-------------|------------|
| 1 | `/` | Webapp (Vue 3) | strip-prefix, headers |
| 50 | `/admin` | Admin Panel | strip-prefix, headers, auth |
| 100 | `/api/v1/*` | API Direct | strip-prefix, headers, cors |
| 200 | `/v1/*` | API Strip | strip-prefix, headers, cors |
| 300 | `/health` | Health Check | headers |
| 400 | `/metrics` | Prometheus | headers, auth |

### SSL/TLS Configuration
```yaml
# SSL Configuration
labels:
  - "traefik.http.routers.webapp-secure.rule=Host(`dating.serge.cc`)"
  - "traefik.http.routers.webapp-secure.entrypoints=websecure"
  - "traefik.http.routers.webapp-secure.tls.certresolver=letsencrypt"
  - "traefik.http.routers.webapp-secure.tls.domains[0].main=dating.serge.cc"
  - "traefik.http.routers.webapp-secure.tls.domains[0].sans=*.dating.serge.cc"
```

## API Gateway Routing

### Service Routing Table
| Service | Internal Port | External Route | Health Check |
|---------|---------------|----------------|--------------|
| auth-service | 8081 | `/v1/auth/*` | `/health` |
| profile-service | 8082 | `/v1/profiles/*` | `/health` |
| discovery-service | 8083 | `/v1/discovery/*` | `/health` |
| chat-service | 8084 | `/v1/chat/*` | `/health` |
| media-service | 8085 | `/v1/media/*` | `/health` |
| admin-service | 8086 | `/v1/admin/*` | `/health` |
| notification-service | 8087 | `/v1/notifications/*` | `/health` |
| data-service | 8088 | `/v1/data/*` | `/health` |

### Gateway Implementation
```python
# gateway/main.py
async def route_request(request):
    """Route requests to appropriate microservices."""
    path = request.path
    method = request.method
    
    # Service routing logic
    if path.startswith('/v1/auth/'):
        return await proxy_to_service(request, 'auth-service', 8081)
    elif path.startswith('/v1/profiles/'):
        return await proxy_to_service(request, 'profile-service', 8082)
    elif path.startswith('/v1/discovery/'):
        return await proxy_to_service(request, 'discovery-service', 8083)
    elif path.startswith('/v1/chat/'):
        return await proxy_to_service(request, 'chat-service', 8084)
    elif path.startswith('/v1/media/'):
        return await proxy_to_service(request, 'media-service', 8085)
    elif path.startswith('/v1/admin/'):
        return await proxy_to_service(request, 'admin-service', 8086)
    elif path.startswith('/v1/notifications/'):
        return await proxy_to_service(request, 'notification-service', 8087)
    elif path.startswith('/v1/data/'):
        return await proxy_to_service(request, 'data-service', 8088)
    else:
        return web.json_response({'error': 'Not Found'}, status=404)

async def proxy_to_service(request, service_name, port):
    """Proxy request to microservice."""
    target_url = f"http://{service_name}:{port}{request.path}"
    
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=request.method,
            url=target_url,
            headers=request.headers,
            data=await request.read()
        ) as response:
            return web.Response(
                body=await response.read(),
                status=response.status,
                headers=response.headers
            )
```

## WebSocket Routing

### WebSocket Proxy Configuration
```python
# gateway/websocket.py
async def websocket_proxy(request):
    """Proxy WebSocket connections to chat service."""
    ws_url = f"ws://chat-service:8084{request.path}"
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await request.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await request.send_bytes(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
```

### WebSocket Routes
| Route | Service | Description |
|-------|---------|-------------|
| `/v1/chat/ws` | chat-service | Real-time messaging |
| `/v1/notifications/ws` | notification-service | Push notifications |

## Load Balancing

### Service Load Balancing
```python
# gateway/load_balancer.py
class ServiceLoadBalancer:
    def __init__(self):
        self.service_instances = {
            'auth-service': ['auth-service-1:8081', 'auth-service-2:8081'],
            'profile-service': ['profile-service-1:8082', 'profile-service-2:8082'],
            'discovery-service': ['discovery-service-1:8083', 'discovery-service-2:8083'],
        }
        self.current_index = {}
    
    def get_next_instance(self, service_name):
        """Round-robin load balancing."""
        instances = self.service_instances.get(service_name, [])
        if not instances:
            return None
        
        index = self.current_index.get(service_name, 0)
        instance = instances[index]
        self.current_index[service_name] = (index + 1) % len(instances)
        return instance
```

### Health Check Integration
```python
# gateway/health_checker.py
class HealthChecker:
    def __init__(self):
        self.healthy_services = set()
        self.check_interval = 30  # seconds
    
    async def check_service_health(self, service_name, port):
        """Check if service is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{service_name}:{port}/health") as response:
                    if response.status == 200:
                        self.healthy_services.add(service_name)
                        return True
                    else:
                        self.healthy_services.discard(service_name)
                        return False
        except Exception:
            self.healthy_services.discard(service_name)
            return False
    
    async def get_healthy_instances(self, service_name):
        """Get only healthy service instances."""
        instances = self.service_instances.get(service_name, [])
        return [inst for inst in instances if inst in self.healthy_services]
```

## Service Discovery

### Docker Network Discovery
```yaml
# docker-compose.yml
networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Service Registration
```python
# gateway/service_registry.py
class ServiceRegistry:
    def __init__(self):
        self.services = {}
        self.health_checks = {}
    
    def register_service(self, name, host, port, health_check_path="/health"):
        """Register a service."""
        self.services[name] = {
            'host': host,
            'port': port,
            'health_check_path': health_check_path,
            'status': 'unknown'
        }
    
    def get_service(self, name):
        """Get service information."""
        return self.services.get(name)
    
    def update_service_status(self, name, status):
        """Update service health status."""
        if name in self.services:
            self.services[name]['status'] = status
```

## Middleware Stack

### Standard Middleware
```python
# gateway/middleware.py
async def cors_middleware(request, handler):
    """CORS middleware."""
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

async def auth_middleware(request, handler):
    """Authentication middleware."""
    if request.path.startswith('/v1/auth/'):
        return await handler(request)
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    
    # Validate JWT token
    token = auth_header.split(' ')[1]
    if not validate_jwt_token(token):
        return web.json_response({'error': 'Invalid token'}, status=401)
    
    return await handler(request)

async def rate_limit_middleware(request, handler):
    """Rate limiting middleware."""
    client_ip = request.remote
    if await is_rate_limited(client_ip):
        return web.json_response({'error': 'Rate limited'}, status=429)
    
    return await handler(request)
```

### Middleware Order
1. **CORS Middleware**: Handle cross-origin requests
2. **Rate Limiting**: Prevent abuse
3. **Authentication**: Validate JWT tokens
4. **Request Logging**: Log all requests
5. **Error Handling**: Catch and format errors
6. **Response Headers**: Add security headers

## Database Routing

### Connection Pooling
```python
# core/database.py
class DatabaseRouter:
    def __init__(self):
        self.pools = {}
        self.pool_size = 20
    
    async def get_pool(self, service_name):
        """Get database connection pool for service."""
        if service_name not in self.pools:
            self.pools[service_name] = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=5,
                max_size=self.pool_size,
                command_timeout=30
            )
        return self.pools[service_name]
    
    async def execute_query(self, service_name, query, *args):
        """Execute query using service-specific pool."""
        pool = await self.get_pool(service_name)
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)
```

### Read/Write Splitting
```python
# core/database_router.py
class ReadWriteRouter:
    def __init__(self):
        self.read_pools = []
        self.write_pool = None
    
    async def get_read_connection(self):
        """Get read-only connection."""
        # Round-robin selection for read replicas
        pool = self.read_pools[self.current_read_index]
        self.current_read_index = (self.current_read_index + 1) % len(self.read_pools)
        return pool
    
    async def get_write_connection(self):
        """Get write connection."""
        return self.write_pool
```

## Monitoring and Observability

### Route Metrics
```python
# gateway/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_connections = Gauge('http_active_connections', 'Active HTTP connections')

# Service metrics
service_health = Gauge('service_health_status', 'Service health status', ['service_name'])
service_response_time = Histogram('service_response_time_seconds', 'Service response time', ['service_name'])
```

### Health Check Endpoints
```python
# gateway/health.py
async def health_check(request):
    """Comprehensive health check."""
    services = ['auth-service', 'profile-service', 'discovery-service', 'chat-service', 'media-service']
    health_status = {}
    
    for service in services:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{service}:8080/health", timeout=5) as response:
                    health_status[service] = {
                        'status': 'healthy' if response.status == 200 else 'unhealthy',
                        'response_time': response.headers.get('X-Response-Time', 'unknown')
                    }
        except Exception as e:
            health_status[service] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    return web.json_response({
        'status': 'healthy' if all(s['status'] == 'healthy' for s in health_status.values()) else 'unhealthy',
        'services': health_status,
        'timestamp': datetime.utcnow().isoformat()
    })
```

## Security Considerations

### Route Security
- **Authentication**: JWT token validation on all protected routes
- **Authorization**: Role-based access control
- **Rate Limiting**: Per-IP and per-user rate limits
- **CORS**: Configured for specific origins
- **SSL/TLS**: All external traffic encrypted

### Internal Security
- **Service Mesh**: Encrypted inter-service communication
- **Network Isolation**: Services isolated in Docker networks
- **Secret Management**: Environment-based secret injection
- **Audit Logging**: All routing decisions logged

## Performance Optimization

### Caching Strategy
```python
# gateway/cache.py
class RouteCache:
    def __init__(self):
        self.cache = {}
        self.ttl = 300  # 5 minutes
    
    async def get_cached_response(self, request):
        """Get cached response if available."""
        cache_key = f"{request.method}:{request.path}:{request.query_string}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return cached_data
        return None
    
    async def cache_response(self, request, response):
        """Cache response for future requests."""
        cache_key = f"{request.method}:{request.path}:{request.query_string}"
        self.cache[cache_key] = (response, time.time())
```

### Connection Pooling
```python
# gateway/connection_pool.py
class ConnectionPoolManager:
    def __init__(self):
        self.pools = {}
        self.max_connections = 100
    
    async def get_connection(self, service_name):
        """Get connection from pool."""
        if service_name not in self.pools:
            self.pools[service_name] = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        return self.pools[service_name]
```

## Troubleshooting

### Common Issues
1. **Service Unavailable**
   - Check service health status
   - Verify network connectivity
   - Check service logs

2. **Routing Failures**
   - Verify route configuration
   - Check middleware order
   - Validate service registration

3. **Performance Issues**
   - Monitor connection pools
   - Check rate limiting
   - Analyze request patterns

### Debugging Tools
```bash
# Check service health
curl http://localhost:8080/health

# Test specific route
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/v1/auth/verify

# Check Traefik dashboard
curl http://localhost:8080/api/http/routers

# Monitor service logs
docker compose logs -f api-gateway
```

## Conclusion

The routing strategy provides a robust, scalable, and secure foundation for the Dating Platform. Key benefits:

- **High Availability**: Load balancing and health checks
- **Security**: Authentication and authorization at the gateway
- **Performance**: Connection pooling and caching
- **Monitoring**: Comprehensive metrics and logging
- **Scalability**: Easy service addition and removal
- **Maintainability**: Clear separation of concerns