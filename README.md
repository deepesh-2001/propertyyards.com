# 🏠 Housing Platform

**Real Estate SaaS** — FastAPI + MongoDB + Redis  
10K+ QPM | 1K+ Users | Microservices

📱 Mobile-friendly docs  
🚀 Quick start below

---

## ⚡ Quick Start

```bash
# One command to start everything
docker-compose up -d

# Access the app
📱 http://localhost      # API Gateway
📖 http://localhost/docs # API Docs
```

**Services:** API (:80) | Auth (:8001) | Property (:8002) | Report (:8004) | MongoDB (:27017) | Redis (:6379)

---

## Features

### 🏢 Core
**Property** — Listings, search, inquiries, brokers, AI prediction, CRM

### 📊 Analytics (NEW)
**Sales** — Track sales, commissions, brokers  
**Projections** — AI market forecasts  
**Growth** — Location demand/supply analysis  
**Projects** — Upcoming developments  
**Investments** — ROI analysis, risk assessment

### 👥 Users
Auth (JWT), RBAC roles, recruitment

### 💰 Finance
Commissions, payroll, tax (India), reimbursements, claims, credit cards

### 🔧 Operations
HR onboarding/offboarding, attendance, notifications, monitoring

### 🛡️ Insurance (NEW)
Health, Life, Property, Home insurance scraped from web with sales integration

### ⚡ Optimized Background (NEW)
- **Idle-time AI Processing** — Beautiful content generated when system idle
- **Sales Fetching** — Limited to 4 times per day (2 AM, 8 AM, 2 PM, 8 PM)
- **Smart Scheduling** — Tasks run only when load < 30%
- **AI Content** — Auto-generate property descriptions, social posts, images
- **Cache Maintenance** — Background cache warming & cleanup
- **Database Optimization** — Index rebuilds during low usage

---

## Architecture

### Microservices

**Gateway** (:80) → Routes to services  
**Auth** (:8001) → JWT, RBAC  
**Property** (:8002) → Listings, search  
**User** (:8003) → Profiles, HR  
**Report** (:8004) → Sales, projections  
**Analytics** (:8006) → AI predictions

**Database:** MongoDB replica set (Primary + Secondary)  
**Cache:** Redis | **Queue:** RabbitMQ

### Caching
- Local (60s) → Redis (5-30min) → MongoDB (1-24hr)

---

## 📚 API Quick Reference

### Auth
`POST /api/auth/login` — Get JWT tokens

### Properties
`GET /api/properties` — List properties  
`POST /api/properties` — Create listing

### Reports (NEW)
`GET /api/reports/sales` — Sales report (CSV/PDF/JSON)  
`GET /api/reports/projections` — Market forecasts  
`GET /api/reports/future-growth` — Growth analysis  
`GET /api/reports/future-projects` — Projects pipeline  
`GET /api/reports/investments` — Investment opportunities  
`POST /api/reports/ai-projection` — AI market forecast

### Finance
`POST /api/commission/calculate` — Calculate commission  
`POST /api/salary/periods/{id}/process` — Run payroll  
`POST /api/tax/compute` — Compute tax

### Insurance (NEW)
`GET /api/insurance/plans` — Scraped insurance plans  
`GET /api/insurance/providers` — Insurance providers  
`POST /api/insurance/recommend` — AI-recommended plans  
`POST /api/insurance/compare` — Compare plans side-by-side  
`POST /api/insurance/sales/{id}/quotes` — Generate sale quotes  
`GET /api/insurance/sales/{id}/summary` — Sale insurance summary  
`GET /api/insurance/dashboard/metrics` — Insurance sales metrics

**Full API docs:** http://localhost/docs

---

## 🚀 Setup Options

### Option 1: Docker (Recommended)
```bash
docker-compose up -d
```

### Option 2: Manual
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend  
cd frontend && npm install && npm run dev
```

---

## ⚙️ Key Environment Variables

```bash
# Required
JWT_SECRET_KEY=your-secret-key
MONGO_ROOT_PASSWORD=db-password
REDIS_PASSWORD=cache-password

# Optional
OPENAI_API_KEY=sk-...      # For AI features
SMTP_HOST=smtp.gmail.com   # For emails
```

**Full list:** See `.env.example`

---

## 📊 Performance

| Metric | Target |
|--------|--------|
| Response (p99) | < 200ms |
| Throughput | 10K+ QPM |
| Concurrent | 1K+ users |
| Cache Hit | > 80% |

### Scale Services
```bash
docker-compose up -d --scale property-service=5
```

---

## 🔒 Security

- JWT authentication (HS256)
- bcrypt password hashing
- HTTPS/TLS via Nginx
- Pydantic input validation
- Role-based access control (RBAC)
- Rate limiting

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

