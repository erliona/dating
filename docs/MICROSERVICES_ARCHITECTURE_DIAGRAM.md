# Microservices Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clients                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Telegram   │  │  Mobile App  │  │   Web App    │          │
│  │    Users     │  │   (Future)   │  │   (Future)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
└─────────┼─────────────────┼──────────────────┼───────────────────┘
          │                 │                  │
          └─────────────────┼──────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Port 8080)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Request Routing                                         │ │
│  │  • Load Balancing                                          │ │
│  │  • Rate Limiting                                           │ │
│  │  • Health Aggregation                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
          ├──────────┬──────────┬──────────┬──────────┬──────────
          ▼          ▼          ▼          ▼          ▼          
┌─────────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐
│Auth Service │ │ Profile │ │Discovery │ │ Media  │ │  Chat   │
│  Port 8081  │ │ Service │ │ Service  │ │Service │ │ Service │
├─────────────┤ │Port 8082│ │Port 8083 │ │Port8084│ │Port 8085│
│             │ ├─────────┤ ├──────────┤ ├────────┤ ├─────────┤
│• JWT Auth   │ │• CRUD   │ │• Matching│ │• Upload│ │• WebSock│
│• Validate   │ │• Photos │ │• Like/   │ │• Store │ │• Message│
│• Refresh    │ │• Profile│ │  Pass    │ │• Serve │ │• History│
│             │ │• Update │ │• Filters │ │• NSFW  │ │• Typing │
└─────────────┘ └────┬────┘ └────┬─────┘ └────┬───┘ └────┬────┘
                     │           │              │          │
                     └───────────┼──────────────┼──────────┘
                                 ▼              │
                        ┌──────────────────┐    │
                        │   PostgreSQL     │◄───┘
                        │    Port 5432     │
                        ├──────────────────┤
                        │• Users           │
                        │• Profiles        │
                        │• Matches         │
                        │• Messages        │
                        │• Photos metadata │
                        └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Telegram Bot Adapter                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Telegram API Integration                                │ │
│  │  • Commands (/start, /profile, /help)                      │ │
│  │  • Mini App Launch                                         │ │
│  │  • Uses API Gateway for all operations                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. User Authentication Flow

```
User → Telegram Mini App → API Gateway → Auth Service
                                              ↓
                                         Validate InitData
                                              ↓
                                         Generate JWT
                                              ↓
                                         Return Token
                                              ↓
User ← Telegram Mini App ← API Gateway ← Auth Service
```

### 2. Profile Creation Flow

```
User → Telegram Mini App → API Gateway → Profile Service
         (with JWT)                            ↓
                                         Verify JWT (via Auth Service)
                                               ↓
                                         Validate Data
                                               ↓
                                         Save to DB ←───┐
                                               ↓        │
                                         PostgreSQL ────┘
                                               ↓
User ← Telegram Mini App ← API Gateway ← Profile Service
```

### 3. Photo Upload Flow

```
User → Telegram Mini App → API Gateway → Media Service
         (with photo)                          ↓
                                         Generate UUID
                                               ↓
                                         Save to Disk
                                               ↓
                                         Return file_id
                                               ↓
User ← Telegram Mini App ← API Gateway ← Media Service
         (displays photo)
```

### 4. Matching Flow

```
User → Telegram Mini App → API Gateway → Discovery Service
         (request candidates)                  ↓
                                         Get User Preferences
                                               ↓
                                         Query Profiles ←───┐
                                               ↓            │
                                         PostgreSQL ────────┘
                                               ↓
                                         Apply Filters
                                               ↓
                                         Calculate Scores
                                               ↓
                                         Return Candidates
                                               ↓
User ← Telegram Mini App ← API Gateway ← Discovery Service
         (shows cards)
```

### 5. Chat Flow

```
User → Telegram Mini App → API Gateway → Chat Service
         (WebSocket)                           ↓
                                         Establish WS
                                               ↓
                                         Store Connection
                                               ↓
                                     ┌─────────┴─────────┐
User A ← Send Message ←              │     Broadcast     │
                                     └─────────┬─────────┘
User B ← Receive Message ←                    ↓
                                         PostgreSQL
                                         (save message)
```

## Service Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                      Service Dependencies                     │
└──────────────────────────────────────────────────────────────┘

API Gateway
    ├── Auth Service      (no dependencies)
    ├── Profile Service   (depends on: database)
    ├── Discovery Service (depends on: database)
    ├── Media Service     (depends on: filesystem)
    └── Chat Service      (depends on: database)

All services depend on:
    • PostgreSQL (shared database - Phase 2)
    • Environment variables (.env)
```

## Port Allocation

| Port | Service | Protocol | Access |
|------|---------|----------|--------|
| 8080 | API Gateway | HTTP | Public |
| 8081 | Auth Service | HTTP | Internal |
| 8082 | Profile Service | HTTP | Internal |
| 8083 | Discovery Service | HTTP | Internal |
| 8084 | Media Service | HTTP | Internal |
| 8085 | Chat Service | HTTP/WS | Internal |
| 5432 | PostgreSQL | TCP | Internal |
| 80/443 | WebApp (nginx) | HTTP/HTTPS | Public |

**Note**: In production, only API Gateway and WebApp should be publicly accessible. All other services should be on an internal network.

## Data Flow

### Profile Data Flow

```
┌──────────┐     ┌─────────────┐     ┌────────────┐
│          │────▶│   Profile   │────▶│            │
│  Client  │     │   Service   │     │ PostgreSQL │
│          │◀────│             │◀────│            │
└──────────┘     └─────────────┘     └────────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │    Media    │
                 │   Service   │
                 │ (references)│
                 └─────────────┘
```

### Matching Data Flow

```
┌──────────┐     ┌─────────────┐     ┌────────────┐
│          │────▶│  Discovery  │────▶│            │
│  Client  │     │   Service   │     │ PostgreSQL │
│          │◀────│             │◀────│            │
└──────────┘     └─────────────┘     └────────────┘
                        │
                        ├────────────┐
                        ▼            ▼
                 ┌─────────────┐  ┌─────────────┐
                 │   Profile   │  │    Chat     │
                 │   Service   │  │   Service   │
                 │  (read data)│  │(create conv)│
                 └─────────────┘  └─────────────┘
```

## Scaling Strategy

### Horizontal Scaling

Services that can be scaled horizontally:

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                           │
│         (handles load balancing automatically)           │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Profile     │ │  Profile     │ │  Profile     │
│  Instance 1  │ │  Instance 2  │ │  Instance 3  │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
               ┌──────────────┐
               │  PostgreSQL  │
               │ (shared DB)  │
               └──────────────┘
```

### Recommended Scaling

Based on typical load:

| Service | Default | Under Load | Notes |
|---------|---------|------------|-------|
| API Gateway | 1 | 2-3 | Single point of entry |
| Auth Service | 1 | 2 | Lightweight, stateless |
| Profile Service | 1 | 3-5 | Heavy read operations |
| Discovery Service | 1 | 3-5 | Complex matching logic |
| Media Service | 1 | 2-3 | I/O intensive |
| Chat Service | 1 | 3-5 | WebSocket connections |

## Future Architecture (Phase 5)

### Database per Service

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Profile    │    │  Discovery   │    │    Chat      │
│   Service    │    │   Service    │    │   Service    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Profile DB  │    │ Discovery DB │    │   Chat DB    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
                    ┌──────────────┐
                    │ Event Bus    │
                    │ (RabbitMQ/   │
                    │  Kafka)      │
                    └──────────────┘
```

### Service Mesh (Optional)

```
┌─────────────────────────────────────────────────────────┐
│                     Service Mesh                         │
│              (Istio / Linkerd / Consul)                  │
│  ┌─────────────────────────────────────────────────────┐│
│  │  • Service Discovery                                 ││
│  │  • Load Balancing                                    ││
│  │  • Circuit Breaker                                   ││
│  │  • Distributed Tracing                               ││
│  │  • mTLS                                              ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Service A  │    │   Service B  │    │   Service C  │
│   + Proxy    │    │   + Proxy    │    │   + Proxy    │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Monitoring Stack                     │
└─────────────────────────────────────────────────────────┘

Services
   ↓ (metrics)
Prometheus ──→ Grafana (dashboards)
   ↓ (alerts)
AlertManager ──→ Notifications

Services
   ↓ (logs)
Loki ──→ Grafana (log explorer)

Services
   ↓ (traces)
Jaeger/Zipkin ──→ Distributed Tracing UI
```

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                      Internet                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Firewall / WAF                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Load Balancer                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  API Gateway                             │
│              (Rate Limiting, JWT)                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Internal Network (VPC)                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Microservices                        │  │
│  │       (Service-to-Service mTLS)                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Database (Private Subnet)                     │
└─────────────────────────────────────────────────────────┘
```

## Deployment Flow

```
┌──────────┐
│Developer │
└────┬─────┘
     │ git push
     ▼
┌──────────────┐
│   GitHub     │
└────┬─────────┘
     │ webhook
     ▼
┌──────────────┐
│GitHub Actions│
└────┬─────────┘
     │ build & test
     ▼
┌──────────────┐
│ Docker Build │
└────┬─────────┘
     │ SSH deploy
     ▼
┌──────────────┐
│   Server     │
└────┬─────────┘
     │ docker compose up
     ▼
┌──────────────────────────────────────────┐
│          Running Services                 │
│  ┌────────────────────────────────────┐  │
│  │  Gateway + 5 Microservices         │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Additional Resources

- [Microservices Deployment Guide](MICROSERVICES_DEPLOYMENT.md)
- [Microservices API Reference](MICROSERVICES_API.md)
- [Microservices Quick Start](../MICROSERVICES_QUICK_START.md)
- [Architecture Migration Guide](ARCHITECTURE_MIGRATION_GUIDE.md)
