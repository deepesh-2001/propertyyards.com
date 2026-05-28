# 🏗️ PropertyYards Microservices Architecture

## 📦 Services Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                      │
│                    Port: 80 / 443 (SSL)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼───┐       ┌─────▼──────┐      ┌────▼────┐
│ Auth  │       │ Property   │      │  User   │
│:8001  │       │ :8002      │      │ :8003   │
└───────┘       └────────────┘      └─────────┘
    │                  │                  │
┌───▼───┐       ┌─────▼──────┐      ┌────▼────┐
│Report │       │ Insurance  │      │   AI    │
│:8004  │       │ :8005      │      │ :8006   │
└───────┘       └────────────┘      └─────────┘
    │                  │                  │
┌───▼───┐       ┌─────▼──────┐
│Notif. │       │ Analytics  │
│:8007  │       │ :8008      │
└───────┘       └────────────┘

Shared Infrastructure:
- MongoDB Replica Set (:27017, :27018, :27019)
- Redis Cache (:6379)
- RabbitMQ (:5672)
```

## 🚀 Services

| Service | Port | Responsibility |
|---------|------|----------------|
| **API Gateway** | 80/443 | Routing, SSL, Rate Limiting |
| **Auth Service** | 8001 | JWT, RBAC, User Auth |
| **Property Service** | 8002 | Listings, Search, CRUD |
| **User Service** | 8003 | Profiles, HR, Preferences |
| **Report Service** | 8004 | Sales, Analytics, Exports |
| **Insurance Service** | 8005 | Insurance scraping, Quotes |
| **AI Service** | 8006 | Image gen, Content, Predictions |
| **Notification Service** | 8007 | Email, SMS, Push |
| **Analytics Service** | 8008 | Metrics, Dashboards, Forecasts |

## 📁 Directory Structure

```
microservices/
├── api-gateway/
│   ├── nginx.conf
│   └── Dockerfile
├── auth-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── property-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── user-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── report-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── insurance-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── ai-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── notification-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── analytics-service/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## 🔧 Local Development

```bash
# Start all services
docker-compose -f microservices/docker-compose.yml up -d

# Start specific service
docker-compose up property-service

# View logs
docker-compose logs -f api-gateway
```

## 🌐 API Routing

```
/api/auth/*      → Auth Service (:8001)
/api/properties/* → Property Service (:8002)
/api/users/*     → User Service (:8003)
/api/reports/*   → Report Service (:8004)
/api/insurance/* → Insurance Service (:8005)
/api/ai/*        → AI Service (:8006)
/api/notifications/* → Notification Service (:8007)
/api/analytics/* → Analytics Service (:8008)
```

## 📊 Deployment

- **Production**: Vercel (Frontend) + Railway/Render (Backend Services)
- **Staging**: Vercel Preview + Docker Compose
- **CI/CD**: GitHub Actions

## 🔗 Inter-Service Communication

- **Synchronous**: HTTP/REST via API Gateway
- **Asynchronous**: RabbitMQ for events
- **Shared State**: Redis Cache, MongoDB

## 📝 Environment Variables

Each service requires:
```
MONGODB_URL=
REDIS_URL=
RABBITMQ_URL=
JWT_SECRET=
SERVICE_NAME=
SERVICE_PORT=
```
