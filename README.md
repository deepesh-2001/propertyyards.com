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

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the full system diagram and component breakdown.

```
housing_platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point, router registration
│   │   ├── schemas.py           # All Pydantic models & enums
│   │   ├── database.py          # Motor (async MongoDB) client
│   │   ├── cache.py             # Redis cache layer
│   │   ├── auth.py              # JWT + RBAC helpers
│   │   ├── commission.py        # Commission engine
│   │   ├── credit_card.py       # Rewards & cashback engine
│   │   ├── salary.py            # Payroll processor + SalaryCalculator
│   │   ├── reimbursement.py     # Expense reimbursement lifecycle
│   │   ├── claims.py            # Claims lifecycle
│   │   ├── tax.py               # Indian IT engine + Form-16
│   │   ├── notification.py      # Multi-channel notification service
│   │   └── routers/
│   │       ├── auth.py          · POST /api/auth/*
│   │       ├── users.py         · GET|PUT /api/users/*
│   │       ├── properties.py    · CRUD /api/properties/*
│   │       ├── inquiries.py     · /api/inquiries/*
│   │       ├── brokers.py       · /api/brokers/*
│   │       ├── commission.py    · /api/commission/*
│   │       ├── credit_card.py   · /api/credit-cards/*
│   │       ├── salary.py        · /api/salary/*
│   │       ├── reimbursement.py · /api/reimbursements/*
│   │       ├── claims.py        · /api/claims/*
│   │       ├── tax.py           · /api/tax/*
│   │       ├── payments.py      · /api/payments/*
│   │       ├── referral.py      · /api/referral/*
│   │       ├── loan_calculator.py · /api/loan/*
│   │       ├── recruitment.py   · /api/recruitment/*
│   │       ├── admin.py         · /api/admin/*
│   │       ├── reports.py       · /api/reports/*
│   │       └── monitoring.py    · /api/monitoring/*
│   ├── tests/
│   │   ├── test_api.py
│   │   └── test_load.py
│   └── requirements.txt
├── tests/                       # Root-level pytest suite
│   ├── conftest.py
│   ├── test_commission_credit_salary.py
│   └── test_integration.py
├── frontend/                    # React + Vite application
├── docker-compose.yml
├── ARCHITECTURE.md              # Mermaid system diagrams
├── FLOWCHARTS.md                # Business-flow diagrams
├── SWAGGER_GUIDE.md             # OpenAPI / Swagger reference
└── pytest.ini
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
| Fraud Detection | `app/routers/fraud_detection.py` | Anomaly scoring on transactions |
| Prediction | `app/routers/prediction.py` | AI price prediction |
| Self-Healing | `app/routers/self_healing.py` | Service health recovery |

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

### Docker (Recommended)

```bash
docker-compose up -d
```

Starts: FastAPI `:8000` · React `:3000` · MongoDB `:27017` · Redis `:6379`

### Interactive Docs

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |

---

## Environment Variables

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
- **Horizontal** — Stateless API, add replicas behind Nginx
- **Read replicas** — MongoDB secondary for analytics queries
- **Connection pooling** — Motor configurable `maxPoolSize`
- **Async everywhere** — `async/await` throughout, no blocking I/O

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

