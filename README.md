# Housing Platform — Real Estate Management System

> **Production-grade** real-estate SaaS built with **FastAPI + MongoDB + Redis**, designed for 10 000+ QPM, 1 000+ concurrent users, and a full HR/Finance back-office.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.x-brightgreen)](https://mongodb.com)
[![Redis](https://img.shields.io/badge/Redis-6.x-red)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Module Overview](#module-overview)
4. [API Reference](#api-reference)
5. [Getting Started](#getting-started)
6. [Environment Variables](#environment-variables)
7. [Running Tests](#running-tests)
8. [Performance & Scalability](#performance--scalability)
9. [Security](#security)
10. [Contributing](#contributing)

---

## Features

### Core Real-Estate
- **Property Listings** — Create, search, filter, wishlist; builder & standard properties
- **Advanced Search** — Location, price range, type, amenities, builder
- **Property Inquiries** — Buyer ↔ Seller messaging thread
- **Broker Management** — Assign brokers, track brokerage commissions
- **AI Prediction** — Price prediction & demand forecasting
- **CRM** — Lead tracking, follow-up, and deal pipeline

### Sales & Investment Analytics
- **Sales Records** — Track property sales, commissions, broker performance, payment methods
- **Projections & Forecasts** — AI-powered market projections with confidence scoring
- **Future Growth Analysis** — Location-based growth projections, demand/supply indices
- **Future Projects Pipeline** — Track upcoming developments, pre-launch projects, completion dates
- **Investment Opportunities** — ROI analysis, risk assessment, funding tracking, investment deals

### User & Access
- **Authentication** — JWT (access + refresh tokens), OTP phone verification
- **RBAC** — buyer · seller · agent · broker · admin · HR · finance roles
- **Recruitment** — Job postings, interview scheduling, candidate pipeline

### Finance & Payroll
- **Commission Engine** — Property sale, builder property, loan, referral, brokerage, credit-card cashback commission types with tiered rates
- **Salary & Payroll** — Components (basic, HRA, DA, TA, bonus), payroll-period processing, salary slips, ESI/PF deductions
- **Reimbursement** — Submit → Review → Approve/Reject → auto-paid via payroll run
- **Claims** — Medical, accident, insurance, commission dispute, salary dispute lifecycle
- **Tax (Indian IT)** — Old & New regime slab tax, surcharge, 4 % cess, Section 80C/80D/80CCD, TDS scheduling, Form-16 generation
- **Payments** — Invoice generation, payment conditions, tax/discount on invoice

### Credit Cards
- **Card Management** — Add, apply, OTP verification
- **Rewards Engine** — Points earning (category multipliers), redemption, cashback processing
- **Comparator** — Best-card-for-category, best-cashback ranking by net return after fee
- **Analytics** — Monthly/quarterly/yearly cashback returns, top spending categories

### HR & Operations
- **Onboarding** — New hire lifecycle with 15-item checklist (documents, EPFO/ESI, equipment, access)
- **Offboarding** — Employee exit with 10-item clearance checklist, settlement, EPFO withdrawal/transfer
- **EPFO/ESI Integration** — Registration, withdrawal, transfer tracking for Indian compliance
- **Attendance** — Check-in/out, leave tracking
- **Performance Reviews** — KPI scoring, review cycles
- **Notifications** — Email, WhatsApp, SMS, push (investment & payroll events)
- **Self-Healing** — Auto-detection and recovery of degraded services
- **Fraud Detection** — Anomaly detection on transactions
- **Monitoring** — Real-time platform health, request metrics

---

## Architecture

### Microservices Architecture

PropertyYards uses a **microservices architecture** with an API Gateway routing requests to specialized services. MongoDB runs as a replica set for high availability.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (Nginx)                            │
│                    Routes: /api/auth → auth-service                    │
│                           /api/properties → property-service           │
│                           /api/reports → report-service                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────┬───────────┼───────────┬───────────────┐
        ▼               ▼           ▼           ▼               ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Auth Service │ │ Property │ │  User    │ │  Report  │ │ Notification │
│   (:8001)    │ │ Service  │ │ Service  │ │ Service  │ │   Service    │
│              ││  (:8002) │ │ (:8003)  │ │ (:8004)  │ │   (:8005)    │
│ JWT + RBAC   │ │ Listings │ │ Profiles │ │ Analytics│ │ Email/SMS    │
└──────────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
                                                        ┌──────────────┐
                                                        │  Analytics   │
                                                        │   Service    │
                                                        │   (:8006)    │
                                                        │ AI/Forecast  │
                                                        └──────────────┘
┌─────────────────────────────────────────────────────────────────────┐
│                    Shared Infrastructure Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │MongoDB      │  │MongoDB      │  │   Redis     │  │  RabbitMQ   │  │
│  │Primary      │  │Secondary  │  │   Cache     │  │   Message   │  │
│  │(:27017)     │  │(:27018)    │  │  (:6379)    │  │  (:5672)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Port | Responsibility |
|---------|------|----------------|
| `api-gateway` | 80/443 | Routes requests, load balancing, SSL termination |
| `auth-service` | 8001 | JWT authentication, RBAC, user sessions |
| `property-service` | 8002 | Property CRUD, search, wishlist, inquiries |
| `user-service` | 8003 | User profiles, HR data, preferences |
| `report-service` | 8004 | Sales, projections, growth, projects, investment reports |
| `notification-service` | 8005 | Email, SMS, WhatsApp, push notifications |
| `analytics-service` | 8006 | AI predictions, market analysis, forecasting |

### Service Manager Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ServiceManager                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   Services   │ │ Health Check │ │ Dependencies │         │
│  │              │ │              │ │              │         │
│  │ - cache      │ │ Status: OK   │ │ cache → db   │         │
│  │ - database   │ │ Status: OK   │ │ db → analytics│         │
│  │ - analytics  │ │ Status: OK   │ │ ai → image   │         │
│  │ - ai_image   │ │              │ │              │         │
│  │ - social     │ │              │ │              │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  UnifiedCacheManager    │   ConnectionPoolManager          │
│  - Local + Redis Cache  │   - MongoDB (100 max)             │
│  - Stats tracking       │   - Redis (50 max)                │
│  - Pattern invalidation │   - HTTP (20 max)                 │
└─────────────────────────────────────────────────────────────┘
```

### Three-Tier Caching Architecture

```
┌─────────────────────────────────────────┐
│  Tier 1: Local Cache (In-Memory)          │
│  - 1000 items, 60s TTL                    │
│  - Sub-millisecond access                 │
├─────────────────────────────────────────┤
│  Tier 2: Redis Cache                      │
│  - 5-30 min TTL                           │
│  - Distributed across instances           │
├─────────────────────────────────────────┤
│  Tier 3: Persistent (MongoDB)             │
│  - 1-24 hour TTL                          │
│  - Survives restarts                      │
└─────────────────────────────────────────┘
```

---

## Module Overview

| Module | File | Purpose |
|--------|------|---------|
| Commission | `app/commission.py` | Calculate & pay commissions (8 types, tiered rates) |
| Credit Card | `app/credit_card.py` | Rewards points, cashback, best-card comparator |
| Salary | `app/salary.py` | Payroll run, net-salary breakdown, salary slips |
| Reimbursement | `app/reimbursement.py` | Expense claim lifecycle, auto-paid in payroll |
| Claims | `app/claims.py` | HR/insurance/dispute claim lifecycle |
| Tax | `app/tax.py` | Indian IT slab tax, TDS, Form-16 |
| Notification | `app/notification.py` | Email, WhatsApp, SMS, push notifications |
| Auth | `app/auth.py` | JWT, OTP, RBAC |
| Service Manager | `app/service_manager.py` | Monolithic service container |
| Unified Startup | `app/unified_startup.py` | Centralized bootstrapper |
| Realtime Analytics | `app/realtime_analytics.py` | Minute-by-minute analytics tracking |
| Predictive Analytics | `app/predictive_analytics.py` | AI forecasting & trend analysis |
| AI Image Service | `app/ai_image_service.py` | DALL-E image generation |
| News Service | `app/news_service.py` | AI article generation from templates |
| Telegram Bot | `app/telegram_bot.py` | Telegram bot for notifications |
| Idle Processor | `app/idle_task_processor.py` | Idle-time background tasks |
| Cache Pipeline | `app/cache_pipeline.py` | Redis pipeline operations |
| Persistent Cache | `app/persistent_cache.py` | MongoDB cache storage |
| DB Optimized | `app/db_optimized.py` | Query optimization & connection pool |
| Security | `app/security.py` | Security middleware & headers |
| WebSocket Manager | `app/websocket_manager.py` | Real-time WebSocket connections |
| Time Series | `app/timeseries.py` | Time-series data storage |
| Cache Decorators | `app/cache_decorators.py` | @cached decorators |
| Fraud Detection | `app/routers/fraud_detection.py` | Anomaly scoring on transactions |
| Prediction | `app/routers/prediction.py` | AI price prediction |
| Self-Healing | `app/routers/self_healing.py` | Service health recovery |
| **Sales Records** | `app/models.py` | Property sales tracking, commissions |
| **Projections** | `app/models.py` | Market forecasts, confidence scoring |
| **Future Growth** | `app/models.py` | Location growth analysis, demand/supply |
| **Future Projects** | `app/models.py` | Upcoming developments, pre-launch |
| **Investment Opp.** | `app/models.py` | ROI analysis, risk assessment |
| **Report Generator** | `app/report_generator.py` | CSV/PDF/JSON report generation |
| **Reports Router** | `app/routers/reports.py` | Sales, projections, investment APIs |

---

## API Reference

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Logout |

### Properties
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/properties` | List (paginated + filtered) |
| POST | `/api/properties` | Create listing |
| GET | `/api/properties/{id}` | Get details |
| PUT | `/api/properties/{id}` | Update listing |
| DELETE | `/api/properties/{id}` | Delete listing |
| POST | `/api/properties/{id}/wishlist` | Add to wishlist |

### Commission
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/commission/rules` | Create commission rule |
| POST | `/api/commission/calculate` | Calculate commission for a deal |
| POST | `/api/commission/payouts` | Process payout |
| GET | `/api/commission/analytics` | Commission analytics |
| GET | `/api/commission/returns/monthly` | Monthly returns |
| GET | `/api/commission/returns/quarterly` | Quarterly returns |
| GET | `/api/commission/returns/yearly` | Yearly returns |

### Credit Cards
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/credit-cards` | Add card |
| GET | `/api/credit-cards/{id}` | Get card |
| POST | `/api/credit-cards/{id}/rewards` | Record reward transaction |
| POST | `/api/credit-cards/{id}/cashback` | Process cashback |
| GET | `/api/credit-cards/best-cashback` | Best cards by net cashback |
| GET | `/api/credit-cards/compare` | Compare cards |
| GET | `/api/credit-cards/analytics/{user_id}` | Reward analytics |

### Salary & Payroll
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/salary/components` | Create salary component |
| POST | `/api/salary/periods` | Create payroll period |
| POST | `/api/salary/periods/{id}/process` | Run payroll (auto-pays reimbursements) |
| POST | `/api/salary/slips` | Generate salary slip |
| GET | `/api/salary/employees/{id}/slips` | Employee's salary slips |

### Reimbursements
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/reimbursements` | Submit expense |
| GET | `/api/reimbursements/{id}` | Get reimbursement |
| GET | `/api/reimbursements/employees/{id}/reimbursements` | Employee's expenses |
| PUT | `/api/reimbursements/{id}/approve` | Approve with amount |
| PUT | `/api/reimbursements/{id}/reject` | Reject with reason |
| GET | `/api/reimbursements/analytics/summary` | Analytics |

### Claims
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/claims` | Open new claim |
| GET | `/api/claims/{id}` | Get claim |
| GET | `/api/claims` | List all claims |
| PUT | `/api/claims/{id}/assign` | Assign investigator |
| PUT | `/api/claims/{id}/resolve` | Resolve claim |
| GET | `/api/claims/analytics/summary` | Analytics |

### Tax
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tax/slabs` | Create custom tax slab |
| GET | `/api/tax/slabs` | List slabs (by regime / FY) |
| POST | `/api/tax/compute` | Compute annual tax liability |
| POST | `/api/tax/form16/{employee_id}` | Generate Form-16 |
| GET | `/api/tax/form16/{employee_id}` | Get employee's Form-16 history |
| GET | `/api/tax/tds/monthly-estimate` | Quick monthly TDS estimate |

### Loan Calculator
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/loan/calculate` | EMI + total cost breakdown |
| POST | `/api/loan/mortgage` | Mortgage with tax & insurance |
| POST | `/api/loan/affordability` | Max affordable price |

### Referral
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/referral/codes` | Create referral code |
| POST | `/api/referral/apply` | Apply referral code |
| POST | `/api/referral/rewards/{id}/claim` | Claim reward |
| GET | `/api/referral/stats` | Referral stats |

### Sales & Investment Reports
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports/sales` | Sales records report (CSV/PDF/JSON) |
| GET | `/api/reports/projections` | Market projections & forecasts |
| GET | `/api/reports/future-growth` | Location growth analysis |
| GET | `/api/reports/future-projects` | Upcoming projects pipeline |
| GET | `/api/reports/investments` | Investment opportunities report |
| POST | `/api/reports/ai-projection` | Generate AI market projection |
| POST | `/api/reports/stakeholder/generate` | Generate stakeholder report |
| GET | `/api/reports/stakeholder/list` | List generated reports |
| GET | `/api/reports/stakeholder/report-types` | Available report types |

### Realtime & WebSocket
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/realtime/dashboard` | Real-time dashboard data |
| GET | `/api/realtime/forecasts` | AI predictions |
| GET | `/api/realtime/market-outlook` | Market forecast |
| WS | `/ws/analytics` | WebSocket for live analytics |
| WS | `/ws/notifications` | WebSocket for notifications |

### Cache Management
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cache/stats` | Cache statistics |
| POST | `/api/cache/warm` | Warm cache |
| POST | `/api/cache/invalidate` | Invalidate by pattern |
| POST | `/api/cache/preload` | Preload popular data |

### Admin Portal
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/portal/dashboard` | Admin dashboard |
| GET | `/api/admin/portal/users/management` | User management |
| GET | `/api/admin/portal/properties/management` | Property management |
| POST | `/api/admin/portal/ai/generate-property-image` | Generate AI images |
| POST | `/api/admin/portal/system/clear-cache` | Clear cache |

### Social Media
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/social-media/dashboard` | Social dashboard |
| POST | `/api/social-media/schedule` | Schedule post |
| POST | `/api/social-media/post-now` | Post immediately |
| POST | `/api/social-media/auto-generate` | Auto-generate posts |
| GET | `/api/social-media/analytics` | Social analytics |

### Telegram
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/telegram/webhook` | Telegram webhook |
| GET | `/api/telegram/subscribers` | List subscribers |
| POST | `/api/telegram/broadcast` | Broadcast message |

### News & Articles
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/news/articles` | List articles |
| GET | `/api/news/articles/{id}` | Get article |
| POST | `/api/news/admin/generate` | Generate AI article |
| POST | `/api/news/admin/rewrite` | Rewrite external article |
| POST | `/api/news/admin/fetch-news` | Fetch external news |
| POST | `/api/news/admin/publish/{id}` | Publish article |

### System Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Application status |
| GET | `/services` | All service statuses |

---

## Getting Started

### Prerequisites
- Python 3.9+
- MongoDB 6.x
- Redis 6+
- Node.js 18+ (frontend)
- Docker & Docker Compose (optional)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # fill in your values
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

### Docker Microservices (Recommended)

```bash
# Start all microservices and infrastructure
docker-compose up -d

# Scale specific services
docker-compose up -d --scale property-service=3 --scale report-service=2
```

**Services Started:**

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | `:80` / `:443` | Nginx reverse proxy, SSL termination |
| Auth Service | `:8001` | JWT authentication, RBAC |
| Property Service | `:8002` | Property listings, search |
| User Service | `:8003` | User profiles, HR data |
| Report Service | `:8004` | Sales, projections, investments |
| Notification Service | `:8005` | Email, SMS, WhatsApp |
| Analytics Service | `:8006` | AI predictions, forecasting |
| Frontend | `:5173` | React development server |
| MongoDB Primary | `:27017` | Main write database |
| MongoDB Secondary | `:27018` | Read replica |
| Redis | `:6379` | Caching & sessions |
| RabbitMQ | `:5672` / `:15672` | Message broker (admin UI)

### Interactive Docs

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |

---

## Environment Variables

### Core Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mongodb://localhost:27017/housing_db` | MongoDB URI |
| `REDIS_URL` | `redis://localhost:6379` | Redis URI |
| `JWT_SECRET_KEY` | *(required)* | JWT signing key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `COMPANY_NAME` | `Housing Platform Pvt Ltd` | Used in Form-16 |
| `SMTP_HOST` | — | Email notifications |
| `SMTP_PORT` | `587` | SMTP port |

### AI & ML Services
| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API for image & article generation |
| `OPENAI_IMAGE_MODEL` | `dall-e-3` | Image generation model |
| `NEWS_AUTHOR_NAME` | `PropertyYards Team` | Author name for AI articles |
| `AUTO_PUBLISH_NEWS` | `false` | Auto-publish generated articles |

### Social Media Integration
| Variable | Default | Description |
|----------|---------|-------------|
| `FACEBOOK_ACCESS_TOKEN` | — | Facebook page token |
| `FACEBOOK_PAGE_ID` | — | Facebook page ID |
| `INSTAGRAM_ACCESS_TOKEN` | — | Instagram API token |
| `TWITTER_API_KEY` | — | Twitter API key |
| `TWITTER_API_SECRET` | — | Twitter API secret |
| `LINKEDIN_ACCESS_TOKEN` | — | LinkedIn API token |

### Telegram Bot
| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `TELEGRAM_WEBHOOK_URL` | — | Webhook URL for Telegram |

### Performance Tuning
| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_DB_CONNECTIONS` | `100` | MongoDB connection pool size |
| `MAX_REDIS_CONNECTIONS` | `50` | Redis connection pool size |
| `MAX_HTTP_CONNECTIONS` | `20` | HTTP client pool size |
| `CACHE_TTL_SHORT` | `300` | Short cache TTL (5 min) |
| `CACHE_TTL_MEDIUM` | `1800` | Medium cache TTL (30 min) |
| `CACHE_TTL_LONG` | `86400` | Long cache TTL (24 hours) |

### Microservices Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | — | Service identifier (auth-service, property-service, etc.) |
| `RABBITMQ_URL` | — | RabbitMQ connection string |
| `RABBITMQ_USER` | `admin` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | — | RabbitMQ password |
| `READ_REPLICA_URL` | — | MongoDB read replica URI |

### MongoDB Replica Set
| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_ROOT_PASSWORD` | — | MongoDB admin password |
| `MONGO_REPLICA_SET_NAME` | `rs0` | Replica set name |

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio anyio

# Run all tests
pytest tests/test_commission_credit_salary.py -v

# Run specific module
pytest tests/test_commission_credit_salary.py::TestTaxEngine -v
pytest tests/test_commission_credit_salary.py::TestReimbursementManager -v
pytest tests/test_commission_credit_salary.py::TestClaimsManager -v
pytest tests/test_commission_credit_salary.py::TestPayrollIntegration -v
```

Test coverage areas:
- Commission rates, tiered calculation, analytics
- Credit-card points, cashback, best-card comparator
- Reimbursement submit / approve / reject / analytics
- Claims create / resolve / analytics
- Tax slab computation (old & new regime), surcharge, rebate 87A, TDS
- Salary calculator (PF, ESI, tax delegation)
- Payroll integration (reimbursements auto-paid in run)

---

## Performance & Scalability

| Metric | Target |
|--------|--------|
| Response time (p99) | < 200 ms |
| Throughput | 10 000+ QPM |
| Concurrent users | 1 000+ |
| Cache hit rate | > 80 % |
| DB query time | O(log n) indexed |

### Caching (Redis)
| Resource | TTL |
|----------|-----|
| Property listings | 1 hr |
| User profiles | 30 min |
| Search results | 5 min |
| Analytics | 15 min |

### Scaling
- **Microservices** — Independently scalable services (auth, property, report, etc.)
- **Horizontal** — Stateless API, add replicas behind API Gateway
- **Read replicas** — MongoDB secondary for analytics queries
- **Connection pooling** — Motor configurable `maxPoolSize`
- **Async everywhere** — `async/await` throughout, no blocking I/O
- **Message Queue** — RabbitMQ for async task processing
- **Service Discovery** — Docker Compose service networking

### Microservices Scaling
```bash
# Scale property service to handle high traffic
docker-compose up -d --scale property-service=5

# Scale report service for batch processing
docker-compose up -d --scale report-service=3

# View service logs
docker-compose logs -f report-service
```

---

## Security

| Layer | Mechanism |
|-------|-----------|
| Authentication | JWT (HS256), refresh token rotation |
| Authorization | RBAC via `get_current_user` dependency |
| Password storage | bcrypt + salt |
| Transport | HTTPS enforced in production (Nginx TLS) |
| Input validation | Pydantic V2 strict models |
| NoSQL injection | Motor parameterised queries only |
| CORS | Configurable `CORS_ORIGINS` |
| Rate limiting | Nginx / FastAPI middleware |

---

## Contributing

```bash
git checkout -b feature/your-feature
git commit -am "feat: describe change"
git push origin feature/your-feature
# Open pull request → CI runs pytest → review → merge
```

## License

MIT License — open source, free to use.

