# DeliverIQ — Last-Mile Delivery Allocation System

A Flask + MySQL system that automatically assigns delivery orders to agents
while respecting time, distance, and profitability constraints.

## Architecture

```
delivery_system/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── extensions.py         # SQLAlchemy instance
│   ├── scheduler.py          # APScheduler cron job (7 AM daily)
│   ├── models/
│   │   └── __init__.py       # Warehouse, Agent, AgentCheckin, Order, Assignment, AllocationRun
│   ├── services/
│   │   ├── allocation_engine.py   # Core greedy nearest-neighbour algorithm
│   │   ├── orchestrator.py        # DB ↔ engine bridge, deferred logic
│   │   └── seed_data.py           # Test data generator (10 WH, 200 agents, ~12k orders)
│   └── routes/
│       ├── warehouses.py
│       ├── agents.py
│       ├── orders.py
│       ├── allocation.py     # /api/allocation/run, /seed, /runs, /agent-summary
│       └── dashboard.py      # / → HTML dashboard + /api/dashboard/stats
├── migrations/
│   └── schema.sql            # Raw MySQL DDL
├── tests/
│   ├── conftest.py
│   ├── test_allocation_engine.py   # Unit tests (no DB needed)
│   └── test_integration.py         # Integration tests (SQLite in-memory)
├── run.py
└── requirements.txt
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL
```bash
mysql -u root -p < migrations/schema.sql
```

### 3. Configure DB connection
Edit `app/__init__.py` — update the `SQLALCHEMY_DATABASE_URI`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost/delivery_db'
)
```

### 4. Run the app
```bash
python run.py
```
Visit http://localhost:5000 for the dashboard.

---

## API Endpoints

### Seed test data
```
POST /api/allocation/seed
{ "date": "2025-01-15" }
```

### Manually trigger allocation
```
POST /api/allocation/run
{ "date": "2025-01-15" }
```

### List past runs
```
GET /api/allocation/runs
```

### Agent summary for a date
```
GET /api/allocation/agent-summary?date=2025-01-15
```

### Orders (filterable)
```
GET /api/orders/?status=pending&date=2025-01-15&warehouse_id=1
```

---

## Allocation Algorithm

**Strategy**: Greedy nearest-neighbour, warehouse-isolated.

1. Group agents and orders by warehouse.
2. For each checked-in agent, loop:
   - Find nearest unassigned order (Haversine distance).
   - Check compliance: `current_km + leg_km + return_km ≤ 100` and `current_mins + leg_mins + return_mins ≤ 600`.
   - If both pass → assign. Else → stop for this agent.
3. Remaining unassigned orders → `status = deferred`, `scheduled_date += 1 day`.

**Profitability tiers**:
| Orders/day | Rate      |
|-----------|-----------|
| < 25      | ₹500 min  |
| 25–49     | ₹35/order |
| 50+       | ₹42/order |

**Constraints**:
- Max 10 hours (600 min) per agent per day
- Max 100 km per agent per day
- 1 km = 5 min travel time
- 5 min per delivery stop

---

## Running Tests

```bash
# Unit tests only (no DB)
pytest tests/test_allocation_engine.py -v

# All tests (SQLite in-memory)
pytest tests/ -v
```

---

## Scheduler

The cron job fires daily at **07:00 AM** using APScheduler's `BackgroundScheduler`.
It calls `run_daily_allocation()` which:
1. Fetches checked-in agents for today.
2. Fetches `pending` + `deferred` orders (including carryovers from prior days).
3. Runs the allocation engine.
4. Persists assignments, updates order statuses, records an `AllocationRun` summary.

---

## Test Data Scale

| Metric              | Value              |
|--------------------|--------------------|
| Warehouses          | 10 (Delhi NCR)     |
| Agents per WH       | 20 (200 total)     |
| Orders per WH/day   | ~1,100–1,200       |
| Total orders/day    | ~12,000            |
| Check-in rate       | ~90%               |
