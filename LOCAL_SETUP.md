# Local Development Setup

## Prerequisites
- Docker Desktop (running)
- Git

---

## 1. Create your `.env` file

Create a file named `.env` in the project root (same folder as `docker-compose.local.yml`):

```
MONGO_ROOT_PASSWORD=localpassword
REDIS_PASSWORD=localpassword
JWT_SECRET_KEY=local-dev-secret-key-change-in-production
ENVIRONMENT=development
DATABASE_URL=mongodb://admin:localpassword@mongodb:27017/housing_db?authSource=admin
REDIS_URL=redis://:localpassword@redis:6379
```

All travel API keys are optional — the app uses mock data automatically when they are empty.

---

## 2. Start with Docker (recommended)

```bash
docker-compose -f docker-compose.local.yml up --build
```

Services started:
| Service   | URL                        |
|-----------|----------------------------|
| Backend   | http://localhost:8000      |
| Frontend  | http://localhost:5173      |
| MongoDB   | mongodb://localhost:27017  |
| Redis     | localhost:6379             |
| API Docs  | http://localhost:8000/docs |

**Stop everything:**
```bash
docker-compose -f docker-compose.local.yml down
```

**Rebuild after code changes:**
```bash
docker-compose -f docker-compose.local.yml up --build backend
```

---

## 3. Run backend WITHOUT Docker (Python directly)

### Step 1 — MongoDB & Redis via Docker only
```bash
docker-compose -f docker-compose.local.yml up mongodb redis -d
```

### Step 2 — Create Python virtualenv
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Create `.env` in the `backend/` folder
```
DATABASE_URL=mongodb://admin:localpassword@localhost:27017/housing_db?authSource=admin
REDIS_URL=redis://:localpassword@localhost:6379
JWT_SECRET_KEY=local-dev-secret-key
ENVIRONMENT=development
```

### Step 5 — Run the server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

---

## 4. Run tests

```bash
cd backend
pytest tests/test_travel_services.py -v
```

---

## 5. Common errors and fixes

| Error | Fix |
|-------|-----|
| `MongoDB connection refused` | Make sure Docker is running: `docker-compose -f docker-compose.local.yml up mongodb -d` |
| `Redis connection refused` | Make sure Redis is running: `docker-compose -f docker-compose.local.yml up redis -d` |
| `Permission denied: /app/logs` | Already fixed — logs fall back to stdout automatically |
| `Module not found: app.xxx` | Run from inside the `backend/` folder, or ensure `PYTHONPATH=backend` is set |
| Port 8000 already in use | Kill existing process: `npx kill-port 8000` or change port in the command |

---

## Why the original docker-compose.yml doesn't work

The original `docker-compose.yml` references per-service Dockerfiles (`services/auth/Dockerfile`, `services/property/Dockerfile`, etc.) that **do not exist** — the app is a monolith, not microservices.

Use `docker-compose.local.yml` instead, which correctly uses `backend/Dockerfile`.
