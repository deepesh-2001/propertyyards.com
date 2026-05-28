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

### 🎨 Interactive Tools (NEW)
**Whiteboard** — Drawing canvas for floor plans, property layouts with save/export  
**3D Structure Generator** — Upload images to generate interactive 3D models (Three.js)  
**Test Suite** — Component testing with sample data

### 🤝 Referral Program (NEW)
**External Referrals** — Public form for anyone to submit referrals  
**Commission Tracking** — 2% default, customizable rates  
**Analytics Dashboard** — PDF/Excel/JSON exports, charts, top referrers  
**Role-Based Access** — Admin/Manager/Agent permissions

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

### Microservices Architecture 🏗️

| Service | Port | Purpose | Deploy URL |
|---------|------|---------|------------|
| **API Gateway** | 80/443 | Routing, SSL, Rate Limit | Vercel |
| **Auth Service** | 8001 | JWT, RBAC, User Auth | Vercel |
| **Property Service** | 8002 | Listings, Search, CRUD | Vercel |
| **User Service** | 8003 | Profiles, HR, Preferences | Vercel |
| **Report Service** | 8004 | Sales, Analytics, Exports | Vercel |
| **Insurance Service** | 8005 | Insurance scraping, Quotes | Vercel |
| **AI Service** | 8006 | Image gen, Content, Predictions | Vercel |
| **Notification Service** | 8007 | Email, SMS, Push | Vercel |
| **Analytics Service** | 8008 | Metrics, Dashboards | Vercel |
| **Pricing Service** | 8009 | Dynamic pricing, subscriptions | Vercel |

**Infrastructure:**  
- **Database:** MongoDB Atlas (replica set)  
- **Cache:** Redis Cloud  
- **Queue:** CloudAMQP (RabbitMQ)  
- **CDN:** Vercel Edge Network  
- **Monitoring:** Built-in health checks

### 🚀 Quick Deploy

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Clone repo
git clone https://github.com/deepesh-2001/propertyyards.com.git
cd propertyyards.com

# 3. Deploy all services
vercel --prod  # Deploys frontend + gateway
# Services auto-deploy via GitHub Actions
```

See [MICROSERVICES_DEPLOY.md](MICROSERVICES_DEPLOY.md) for detailed deployment guide.

### 💰 Dynamic Pricing (NEW)

| Feature | Description | Admin Control |
|---------|-------------|---------------|
| Subscription Plans | Free, Basic($9.99), Pro($29.99), Enterprise($99.99) | ✅ Create/Edit/Delete |
| Commission Rates | 2% default, tiered by property value | ✅ Update rates |
| Service Fees | Custom fees per service type | ✅ Configure |
| Discounts | Percentage-based dynamic discounts | ✅ Apply/Remove |
| Price Multipliers | Market-adjustment multipliers | ✅ Set 0.5x-3x |
| Price History | Track all price changes | ✅ View audit log |
| Bulk Updates | Update multiple prices at once | ✅ Admin only |

**Pricing API:**
- `GET /pricing/rules` — List pricing rules
- `POST /pricing/rules` — Create new rule
- `PUT /pricing/rules/{id}` — Update rule
- `POST /pricing/calculate` — Calculate dynamic price
- `POST /pricing/bulk-update` — Bulk price changes

### 🔄 CI/CD Pipeline

- **PR**: Auto preview deployment + tests
- **Merge**: Auto production deployment
- **Monitoring**: Health checks every 6 hours
- **Rollback**: One-click via Vercel dashboard

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

### Whiteboard & 3D (NEW)
`GET /whiteboard` — Drawing canvas tool  
`POST /whiteboard/save` — Save whiteboard drawing  
`GET /3d-structure` — 3D model generator  
`POST /3d-structure/generate` — Generate 3D from image

### Referrals (NEW)
`GET /submit-referral` — Public referral form  
`GET /referrals` — Manage referrals (admin/agent)  
`POST /referrals/{id}/status` — Update referral status  
`GET /analytics` — Referral analytics dashboard  
`POST /analytics/export` — Export PDF/Excel/JSON  
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

# Pricing Service (NEW)
cd microservices/pricing-service
pip install fastapi uvicorn motor redis
uvicorn main:app --port 8009
```

---

## ⚙️ Key Environment Variables

```bash
# Required
JWT_SECRET_KEY=your-secret-key
MONGO_ROOT_PASSWORD=db-password
REDIS_PASSWORD=cache-password

# Microservices
PRICING_API_URL=http://localhost:8009  # Pricing service

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

