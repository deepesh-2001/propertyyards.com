# 🏠 PropertyYards Platform

**Real Estate SaaS** — FastAPI + MongoDB + Redis + Kubernetes  
10K+ QPM | 1K+ Concurrent Users | Microservices | CI/CD on AWS EKS

---

## ⚡ Quick Start

```bash
# One command to start everything
docker-compose up -d

# Access the app
http://localhost        # API Gateway
http://localhost/docs   # Swagger UI (dev only)
```

**Local services:** API Gateway (:80) | Auth (:8001) | Property (:8002) | User (:8003) | Report (:8004) | Notification (:8005) | Analytics (:8006) | MongoDB (:27017) | Redis (:6379) | RabbitMQ (:15672)

---

## Features

### 🏢 Core Property
- Listings, search, CRUD, inquiries, brokers, CRM
- AI price prediction & market forecasting
- Property comparison engine
- Property onboarding workflow

### 👥 Users & Auth
- JWT authentication (HS256) + refresh tokens
- RBAC roles: admin, manager, agent, devops
- Recruitment, onboarding/offboarding, attendance

### 💰 Finance
- Commissions (tiered by property value), payroll, tax (India/RBI compliance)
- Reimbursements, claims, credit cards, cashback & rewards
- Multi-gateway payments: Stripe, Razorpay, PayPal, PayU, Square, Braintree, Mollie
- Ticket booking with loyalty rewards

### 📊 Analytics & Reports
- Sales records, market projections, growth analysis
- Projects pipeline, investment ROI & risk assessment
- AI-powered forecasts via Google Gemini

### 🛡️ Insurance
- Health, Life, Property & Home insurance
- Web-scraped plans from providers
- AI-recommended plans, comparison, sale quotes

### 🤖 AI & Automation
- Google Gemini (image gen, content, projections)
- AI SEO analysis, auto-optimization, keyword tracking
- Competitor analysis vs Zillow, Realtor.com, Redfin
- Idle-time background AI content generation (load < 30%)

### 📣 Marketing & Outreach
- Social media scheduling (Facebook, Instagram, Twitter, LinkedIn)
- Telegram bot integration
- AI-generated news articles & property descriptions
- WhatsApp notifications

### 🎨 Interactive Tools
- Whiteboard canvas — floor plans, property layouts (save/export)
- Referral program — public form, commission tracking, analytics dashboard (PDF/Excel/JSON)
- Feature flags for controlled rollouts
- Architecture & deployment visualization

### ⚡ Background Processing
- Sales fetch: 4×/day (2 AM, 8 AM, 2 PM, 8 PM)
- Smart scheduling: tasks run only when load < 30%
- Cache warming, cleanup, DB index rebuilds

---

## Architecture

### Microservices

| Service | Port | Purpose |
|---------|------|---------|
| **API Gateway** | 80/443 | Nginx routing, SSL, rate limiting |
| **Auth Service** | 8001 | JWT, RBAC, authentication |
| **Property Service** | 8002 | Listings, search, CRUD |
| **User Service** | 8003 | Profiles, HR, preferences |
| **Report Service** | 8004 | Sales, analytics, exports |
| **Notification Service** | 8005 | Email, SMS, WhatsApp, push |
| **Analytics Service** | 8006 | AI metrics, dashboards |

**Infrastructure:**
- **Database:** MongoDB 7 replica set (primary + secondary + arbiter)
- **Cache:** Redis 7 (session store + cache pipeline)
- **Queue:** RabbitMQ (async inter-service messaging)
- **Container Orchestration:** Kubernetes on AWS EKS (`ap-south-1`)
- **Image Registry:** GitHub Container Registry (GHCR)
- **Frontend:** Vercel (React + Vite)

### Caching Strategy
Local (60s) → Redis (5–30 min) → MongoDB (1–24 hr)

---

## 🚀 Deployment

### CI/CD Pipeline (GitHub Actions)

| Trigger | Action |
|---------|--------|
| Pull Request | Run tests → build images → deploy preview to Vercel |
| Push to `main` | Run tests → build & push to GHCR → inject secrets → deploy to EKS → rollout wait |

**Workflow files:**
- `.github/workflows/deploy.yml` — build, push, EKS deploy
- `.github/workflows/ci-cd.yml` — microservices test matrix + Vercel frontend

### Kubernetes (AWS EKS)

```bash
# Apply manifests
cd k8s
kustomize build . | kubectl apply -f -

# Check rollout
kubectl rollout status deployment/propertyyards-api -n production

# Scale manually
kubectl scale deployment propertyyards-api --replicas=5 -n production
```

Auto-scaling: HPA configured — min 3, max 10 replicas (CPU 70% / Memory 80% thresholds).

### Docker Compose (Local / Staging)

```bash
docker-compose up -d
docker-compose up -d --scale property-service=5
```

---

## ⚙️ Environment Variables

All secrets are injected into Kubernetes via the CI/CD pipeline from **GitHub Repository Secrets**.  
For local development, create a `.env` file in `backend/`:

### Required

```bash
DATABASE_URL=mongodb://localhost:27017/housing_db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### AI & Integrations

```bash
GEMINI_API_KEY=             # Google Gemini (AI image/content/projections)
OPENAI_API_KEY=             # Legacy OpenAI (optional)
FIRECRAWL_API_KEY=          # Web scraping (insurance, news)
TELEGRAM_BOT_TOKEN=         # Telegram bot
WHATSAPP_API_KEY=           # WhatsApp notifications
WHATSAPP_PHONE_NUMBER_ID=
```

### Email

```bash
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDGRID_API_KEY=           # Optional SendGrid
MAILGUN_API_KEY=            # Optional Mailgun
MAILGUN_DOMAIN=
```

### Payments

```bash
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYU_MERCHANT_KEY=
PAYU_MERCHANT_SALT=
SQUARE_ACCESS_TOKEN=
BRAINTREE_MERCHANT_ID=
BRAINTREE_PUBLIC_KEY=
BRAINTREE_PRIVATE_KEY=
MOLLIE_API_KEY=
```

### Storage & CDN

```bash
# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
AWS_S3_BUCKET=

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Social Media

```bash
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=
INSTAGRAM_ACCESS_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=
LINKEDIN_ACCESS_TOKEN=
```

### Deployment (GitHub Secrets for CI/CD)

Add these in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `MONGODB_URL` | Full MongoDB connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | JWT signing secret |
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `SMTP_USERNAME` | SMTP email username |
| `SMTP_PASSWORD` | SMTP email password |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret |
| `RAZORPAY_KEY_ID` | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret |
| `AWS_ACCESS_KEY_ID` | AWS access key (EKS + S3) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `SENDGRID_API_KEY` | SendGrid API key |
| `WHATSAPP_API_KEY` | WhatsApp API key |
| `FACEBOOK_ACCESS_TOKEN` | Facebook page access token |
| `FIRECRAWL_API_KEY` | Firecrawl scraping key |
| `VERCEL_TOKEN` | Vercel deploy token |
| `VERCEL_ORG_ID` | Vercel org ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |
| `RAILWAY_TOKEN` | Railway deploy token |
| `SLACK_WEBHOOK_URL` | Slack deployment notifications |

---

## 📚 API Quick Reference

### Auth
`POST /api/auth/login` — Get JWT tokens  
`POST /api/auth/refresh` — Refresh access token

### Properties
`GET /api/properties` — List/search properties  
`POST /api/properties` — Create listing  
`GET /api/comparison` — Compare properties side-by-side

### Reports
`GET /api/reports/sales` — Sales report (CSV/PDF/JSON)  
`GET /api/reports/projections` — Market forecasts  
`GET /api/reports/future-growth` — Growth analysis  
`GET /api/reports/investments` — Investment opportunities  
`POST /api/reports/ai-projection` — AI market forecast

### Finance
`POST /api/commission/calculate` — Calculate commission  
`POST /api/salary/periods/{id}/process` — Run payroll  
`POST /api/tax/compute` — Compute India tax  
`POST /api/payments/charge` — Process payment  
`GET /api/cashback` — Cashback balance  
`GET /api/rewards` — Loyalty rewards  
`GET /api/tickets` — Ticket bookings

### Insurance
`GET /api/insurance/plans` — Scraped insurance plans  
`POST /api/insurance/recommend` — AI-recommended plans  
`POST /api/insurance/compare` — Compare plans  
`GET /api/insurance/dashboard/metrics` — Sales metrics

### Deployment & Ops
`POST /api/deployment/deploy` — Deploy a service (admin)  
`POST /api/deployment/rollback` — Rollback service  
`POST /api/deployment/scale` — Scale replicas  
`GET /api/deployment/history` — Deployment history  
`GET /health` — Application health  
`GET /monitoring/performance` — API performance stats  
`GET /monitoring/system` — System resource stats  
`GET /scaling/status` — Auto-scaling status  
`GET /healing/status` — Auto-healing status

### AI & SEO
`POST /ai/generate-image` — AI property image  
`POST /ai/generate-article` — AI news article  
`POST /seo/analyze` — AI SEO analysis  
`POST /seo/optimize` — Auto-optimize site  
`GET /seo/keywords/suggestions` — Keyword research  
`GET /seo/competitors/analyze` — Competitor analysis

**Full Swagger UI:** `http://localhost/docs` (dev mode only)

---

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Response p99 | < 200ms |
| Throughput | 10K+ QPM |
| Concurrent users | 1K+ |
| Cache hit rate | > 80% |
| Uptime | 99.9% |

---

## 🔒 Security

- JWT HS256 + refresh token rotation
- bcrypt password hashing
- HTTPS/TLS enforced (HSTS, HTTPS redirect middleware)
- Pydantic input validation
- RBAC with role hierarchy
- Rate limiting (1000 req/min global, 100 req/min per user)
- RBI compliance: KYC, PAN verification, transaction limits, fraud detection
- 2FA enforcement for high-value transactions

---

## 🧪 Testing

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## 📝 License

MIT License — Open source, free to use.

**Made with** ❤️ **by PropertyYards Team**

