"""
Seed / Test Data Generator
===========================
Generates simulated data for:
  - 10 warehouses in Delhi NCR
  - 20 agents per warehouse (200 total)
  - Up to 60 orders per agent per day (~12,000 orders)
"""

import random
import string
from datetime import date, datetime
from faker import Faker

fake = Faker('en_IN')

# 10 real-ish warehouse locations around Delhi NCR
WAREHOUSE_LOCATIONS = [
    ("WH-Connaught Place",    28.6315, 77.2167),
    ("WH-Dwarka",             28.5921, 77.0460),
    ("WH-Noida Sector 62",    28.6278, 77.3649),
    ("WH-Gurgaon Cyber City", 28.4950, 77.0890),
    ("WH-Rohini",             28.7041, 77.1025),
    ("WH-Lajpat Nagar",       28.5672, 77.2432),
    ("WH-Janakpuri",          28.6288, 77.0832),
    ("WH-Shahdara",           28.6700, 77.2897),
    ("WH-Faridabad",          28.4089, 77.3178),
    ("WH-Ghaziabad",          28.6692, 77.4538),
]


def random_nearby_coords(base_lat: float, base_lon: float, radius_km: float = 8.0):
    """Generate a random coordinate within radius_km of base."""
    # Approximate: 1 degree lat ≈ 111 km
    delta_lat = random.uniform(-radius_km / 111, radius_km / 111)
    delta_lon = random.uniform(-radius_km / (111 * abs(math.cos(math.radians(base_lat)))), 
                                radius_km / (111 * abs(math.cos(math.radians(base_lat)))))
    return round(base_lat + delta_lat, 6), round(base_lon + delta_lon, 6)


def gen_order_number():
    return 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def seed_database(db, target_date: date = None):
    """Populate DB with test data. Safe to call multiple times (idempotent for warehouses)."""
    import math
    from app.models import Warehouse, Agent, AgentCheckin, Order

    if target_date is None:
        target_date = date.today()

    # ── Warehouses ──────────────────────────────────────────────────────────
    warehouses = []
    for name, lat, lon in WAREHOUSE_LOCATIONS:
        wh = Warehouse.query.filter_by(name=name).first()
        if not wh:
            wh = Warehouse(name=name, city='Delhi NCR', latitude=lat, longitude=lon)
            db.session.add(wh)
    db.session.flush()

    warehouses = Warehouse.query.all()

    # ── Agents ──────────────────────────────────────────────────────────────
    for wh in warehouses:
        existing_count = Agent.query.filter_by(warehouse_id=wh.id).count()
        needed = 20 - existing_count
        for _ in range(needed):
            agent = Agent(
                name=fake.name(),
                phone=fake.phone_number()[:15],
                warehouse_id=wh.id,
                is_active=True,
            )
            db.session.add(agent)
    db.session.flush()

    # ── Agent Check-ins ──────────────────────────────────────────────────────
    all_agents = Agent.query.filter_by(is_active=True).all()
    for agent in all_agents:
        existing = AgentCheckin.query.filter_by(
            agent_id=agent.id, checkin_date=target_date
        ).first()
        if not existing:
            # 90% check-in rate
            if random.random() < 0.90:
                checkin = AgentCheckin(
                    agent_id=agent.id,
                    checkin_date=target_date,
                    checkin_time=datetime.combine(
                        target_date,
                        datetime.strptime(
                            f"0{random.randint(6,8)}:{random.randint(0,59):02d}", "%H:%M"
                        ).time()
                    ),
                    is_available=True,
                )
                db.session.add(checkin)
    db.session.flush()

    # ── Orders ───────────────────────────────────────────────────────────────
    import math
    orders_created = 0
    for wh in warehouses:
        # 60 orders per agent × 20 agents = 1200 per warehouse, ~12000 total
        n_orders = random.randint(1100, 1200)
        for _ in range(n_orders):
            lat, lon = random_nearby_coords(wh.latitude, wh.longitude, radius_km=7.0)
            order = Order(
                order_number=gen_order_number(),
                customer_name=fake.name(),
                customer_phone=fake.phone_number()[:15],
                delivery_address=fake.address(),
                latitude=lat,
                longitude=lon,
                warehouse_id=wh.id,
                weight_kg=round(random.uniform(0.2, 15.0), 2),
                status='pending',
                scheduled_date=target_date,
                deferred_count=0,
            )
            db.session.add(order)
            orders_created += 1

    db.session.commit()
    return {
        'warehouses': len(warehouses),
        'agents': len(all_agents),
        'orders_created': orders_created,
        'target_date': str(target_date),
    }
