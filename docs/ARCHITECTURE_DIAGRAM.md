# Architecture Diagrams

Visual representation of the new architecture.

## Overall Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Telegram   │  │  iOS/Android │  │   Web App    │  (Future) │
│  │   Mini App   │  │    (Future)  │  │   (Future)   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                    │
└─────────┼─────────────────┼──────────────────┼────────────────────┘
          │                 │                  │
          └─────────────────┴──────────────────┘
                            │
                   ┌────────▼─────────┐
                   │   API GATEWAY    │
                   │   (Port 8080)    │
                   └────────┬─────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐
│ Auth Service│      │  Profile   │      │ Discovery  │
│ (Port 8081) │      │  Service   │      │  Service   │
│             │      │ (Port 8082)│      │ (Port 8083)│
│ - JWT       │      │ - Profiles │      │ - Matching │
│ - Sessions  │      │ - Photos   │      │ - Filters  │
└─────────────┘      └────────────┘      └────────────┘
       │                    │                    │
       │             ┌──────┴──────┐             │
       │             │             │             │
┌──────▼──────┐  ┌──▼─────┐  ┌───▼─────┐  ┌────▼───────┐
│    Chat     │  │ Media  │  │  Core   │  │ Adapters   │
│   Service   │  │Service │  │ Logic   │  │            │
│ (Port 8085) │  │(8084)  │  │         │  │            │
│             │  │        │  │         │  │            │
│ - WebSocket │  │ - Upload│ │Services │  │ Platform   │
│ - Messages  │  │ - NSFW  │ │Models   │  │ Specific   │
└─────────────┘  └─────────┘ │Interface│  └────────────┘
       │             │         └─────────┘        │
       │             │              │             │
       └─────────────┴──────────────┴─────────────┘
                            │
                   ┌────────▼─────────┐
                   │   PostgreSQL     │
                   │   Database       │
                   └──────────────────┘
```

## Core Module Structure

```
┌────────────────────────────────────────────────────────┐
│                    CORE MODULE                          │
│              (Platform Independent)                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              MODELS                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │   User   │  │  Profile │  │ Settings │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘      │  │
│  │  ┌──────────────────────────────────────┐      │  │
│  │  │ Enums: Gender, Orientation, Goal... │      │  │
│  │  └──────────────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │              SERVICES                             │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │ UserService  │  │ProfileService│             │  │
│  │  │              │  │              │             │  │
│  │  │ - Create     │  │ - Create     │             │  │
│  │  │ - Ban/Unban  │  │ - Update     │             │  │
│  │  │ - Delete     │  │ - Photos     │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  │  ┌──────────────────────────┐                   │  │
│  │  │   MatchingService        │                   │  │
│  │  │                          │                   │  │
│  │  │ - Recommendations        │                   │  │
│  │  │ - Compatibility Score    │                   │  │
│  │  │ - Apply Filters          │                   │  │
│  │  └──────────────────────────┘                   │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │             INTERFACES                            │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │IUserRepos.   │  │IProfileRepos.│             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │INotification │  │  IStorage    │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │               UTILS                               │  │
│  │  - Age validation                                 │  │
│  │  - Name validation                                │  │
│  │  - Email validation                               │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## Adapter Layer

```
┌────────────────────────────────────────────────────────┐
│                 ADAPTER LAYER                           │
│            (Platform Specific)                          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │          TELEGRAM ADAPTER                          │ │
│  │                                                    │ │
│  │  ┌──────────────────┐  ┌──────────────────────┐  │ │
│  │  │TelegramUser      │  │TelegramProfile       │  │ │
│  │  │Repository        │  │Repository            │  │ │
│  │  │                  │  │                      │  │ │
│  │  │implements        │  │implements            │  │ │
│  │  │IUserRepository   │  │IProfileRepository    │  │ │
│  │  └──────────────────┘  └──────────────────────┘  │ │
│  │                                                    │ │
│  │  ┌──────────────────┐  ┌──────────────────────┐  │ │
│  │  │Telegram          │  │Telegram              │  │ │
│  │  │NotificationSvc   │  │StorageService        │  │ │
│  │  │                  │  │                      │  │ │
│  │  │implements        │  │implements            │  │ │
│  │  │INotificationSvc  │  │IStorageService       │  │ │
│  │  └──────────────────┘  └──────────────────────┘  │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │          MOBILE ADAPTER (Future)                   │ │
│  │  - iOS Push Notifications                          │ │
│  │  - Android Push Notifications                      │ │
│  │  - Mobile Storage (AWS S3)                         │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │          WEB ADAPTER (Future)                      │ │
│  │  - Browser Notifications                           │ │
│  │  - Web Storage (CDN)                               │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Service Communication

```
┌──────────────────────────────────────────────────────────┐
│                    API GATEWAY                            │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  - JWT Authentication                               │  │
│  │  - Rate Limiting                                    │  │
│  │  - Request Routing                                  │  │
│  │  - Load Balancing                                   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────────┘
               │
       ┌───────┴────────┬──────────┬──────────┬──────────┐
       │                │          │          │          │
   ┌───▼───┐      ┌────▼───┐  ┌───▼───┐  ┌──▼───┐  ┌───▼───┐
   │ Auth  │      │Profile │  │Discov.│  │Chat  │  │ Media │
   │Service│      │Service │  │Service│  │Svc   │  │Service│
   └───┬───┘      └────┬───┘  └───┬───┘  └──┬───┘  └───┬───┘
       │               │          │         │          │
       │    HTTP REST  │   HTTP   │  WS     │   HTTP   │
       │   Async Msgs  │   Queue  │  Redis  │   Queue  │
       └───────────────┴──────────┴─────────┴──────────┘
                            │
                   ┌────────▼─────────┐
                   │  Message Queue   │
                   │  (RabbitMQ/Redis)│
                   └──────────────────┘
```

## Request Flow Example: Create Profile

```
1. Client Request
   ┌─────────────┐
   │ Telegram    │
   │ Mini App    │
   └──────┬──────┘
          │ POST /profiles
          │ {name, birth_date, ...}
          │
2. API Gateway
   ┌──────▼──────┐
   │API Gateway  │ ── Verify JWT
   └──────┬──────┘ ── Rate limit check
          │ ── Route to service
          │
3. Profile Service
   ┌──────▼──────────┐
   │Profile Service  │
   │                 │
   │ ┌─────────────┐ │
   │ │ProfileSvc   │ │ ── Validate age
   │ │  (Core)     │ │ ── Business rules
   │ └─────┬───────┘ │
   │       │         │
   │ ┌─────▼───────┐ │
   │ │Telegram     │ │ ── Save to DB
   │ │ProfileRepo  │ │ ── via adapter
   │ └─────────────┘ │
   └──────┬──────────┘
          │
4. Database
   ┌──────▼──────┐
   │ PostgreSQL  │ ── Profile saved
   └─────────────┘
          │
5. Response
   ┌─────▼───────┐
   │  Success    │ ── 201 Created
   │  {profile}  │ ── Return to client
   └─────────────┘
```

## Deployment Architecture

```
┌────────────────────────────────────────────────────────┐
│                   KUBERNETES CLUSTER                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              INGRESS CONTROLLER                   │  │
│  │              (Load Balancer)                      │  │
│  └─────────────────┬────────────────────────────────┘  │
│                    │                                    │
│  ┌─────────────────▼────────────────────────────────┐  │
│  │              API GATEWAY POD                      │  │
│  │              (3 replicas)                         │  │
│  └─────────────────┬────────────────────────────────┘  │
│                    │                                    │
│     ┌──────────────┼──────────────┐                    │
│     │              │               │                    │
│  ┌──▼────┐    ┌───▼────┐    ┌────▼───┐                │
│  │Auth   │    │Profile │    │Discov. │                │
│  │Pods   │    │Pods    │    │Pods    │                │
│  │(3x)   │    │(5x)    │    │(10x)   │ Scale by load  │
│  └───────┘    └────────┘    └────────┘                │
│                                                         │
│  ┌─────────┐    ┌──────────┐                           │
│  │Chat     │    │Media     │                           │
│  │Pods     │    │Pods      │                           │
│  │(8x)     │    │(4x)      │                           │
│  └─────────┘    └──────────┘                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         PostgreSQL StatefulSet                    │  │
│  │         (Primary + Replicas)                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Redis Cluster                             │  │
│  │         (Cache + Pub/Sub)                         │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## Data Flow: Matching Algorithm

```
┌─────────────────────────────────────────────────────────┐
│              MATCHING ALGORITHM FLOW                     │
│                                                          │
│  1. User Opens Discovery                                 │
│     ┌─────────┐                                          │
│     │ Client  │ GET /discovery/candidates               │
│     └────┬────┘                                          │
│          │                                               │
│  2. Discovery Service                                    │
│     ┌────▼─────────────────────────────────┐            │
│     │ Discovery Service                    │            │
│     │                                       │            │
│     │ ┌───────────────────────────────┐   │            │
│     │ │ MatchingService (Core)        │   │            │
│     │ │                               │   │            │
│     │ │ 1. Get user settings          │   │            │
│     │ │    - Age range (25-35)        │   │            │
│     │ │    - Distance (50km)          │   │            │
│     │ │    - Show me (Female)         │   │            │
│     │ │                               │   │            │
│     │ │ 2. Search profiles            │   │            │
│     │ │    - Filter by age            │   │            │
│     │ │    - Filter by gender         │   │            │
│     │ │    - Filter by distance       │   │            │
│     │ │    - Exclude seen profiles    │   │            │
│     │ │                               │   │            │
│     │ │ 3. Calculate compatibility    │   │            │
│     │ │    - Common interests: 16pts  │   │            │
│     │ │    - Same goal: 20pts         │   │            │
│     │ │    - Similar education: 20pts │   │            │
│     │ │    - Common languages: 20pts  │   │            │
│     │ │                               │   │            │
│     │ │ 4. Sort by score              │   │            │
│     │ │    - Best matches first       │   │            │
│     │ └───────────────────────────────┘   │            │
│     └─────────────────────────────────────┘            │
│          │                                               │
│  3. Return Candidates                                    │
│     ┌────▼────────────────────────────────┐             │
│     │ Response: [Profile1, Profile2...]  │             │
│     │ Sorted by compatibility score      │             │
│     └────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## Legend

### Components
- `┌─┐` - Service/Component
- `│ │` - Container boundaries
- `───` - Data flow/connection
- `▼` - Direction of flow

### Ports
- `8080` - API Gateway
- `8081` - Auth Service
- `8082` - Profile Service
- `8083` - Discovery Service
- `8084` - Media Service
- `8085` - Chat Service

### Communication Types
- HTTP REST - Synchronous request/response
- WebSocket (WS) - Real-time bidirectional
- Message Queue - Asynchronous events
- Redis Pub/Sub - Event broadcasting

---

**Last Updated**: 2024-01-10  
**Version**: 1.0.0
