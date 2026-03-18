"""
Integration Tests — Flask API Routes
======================================
Uses in-memory SQLite for speed.
"""

import pytest
from datetime import date
from app import create_app
from app.extensions import db as _db


TEST_CONFIG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': 'test',
}


@pytest.fixture(scope='session')
def app():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        _db.create_all()
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


# ── Warehouse endpoints ───────────────────────────────────────────────────────

def test_create_warehouse(client):
    res = client.post('/api/warehouses/', json={
        'name': 'WH-Test', 'city': 'Delhi', 'latitude': 28.63, 'longitude': 77.22
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['name'] == 'WH-Test'


def test_list_warehouses(client):
    res = client.get('/api/warehouses/')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


# ── Agent endpoints ───────────────────────────────────────────────────────────

def test_create_agent(client):
    # First create a warehouse
    wh_res = client.post('/api/warehouses/', json={
        'name': 'WH-Agent-Test', 'city': 'Delhi', 'latitude': 28.6, 'longitude': 77.2
    })
    wh_id = wh_res.get_json()['id']

    res = client.post('/api/agents/', json={
        'name': 'Ravi Kumar', 'phone': '9876543210', 'warehouse_id': wh_id
    })
    assert res.status_code == 201
    assert res.get_json()['name'] == 'Ravi Kumar'


def test_checkin_agent(client):
    wh_res = client.post('/api/warehouses/', json={
        'name': 'WH-CI', 'city': 'Delhi', 'latitude': 28.6, 'longitude': 77.2
    })
    wh_id = wh_res.get_json()['id']
    ag_res = client.post('/api/agents/', json={
        'name': 'Priya S', 'warehouse_id': wh_id
    })
    ag_id = ag_res.get_json()['id']

    res = client.post(f'/api/agents/{ag_id}/checkin')
    assert res.status_code in (200, 201)
    assert 'checkin' in res.get_json()


# ── Order endpoints ───────────────────────────────────────────────────────────

def test_create_order(client):
    wh_res = client.post('/api/warehouses/', json={
        'name': 'WH-Ord', 'city': 'Delhi', 'latitude': 28.63, 'longitude': 77.22
    })
    wh_id = wh_res.get_json()['id']

    res = client.post('/api/orders/', json={
        'order_number': 'ORD-TEST-001',
        'customer_name': 'Test Customer',
        'latitude': 28.64,
        'longitude': 77.23,
        'warehouse_id': wh_id,
        'scheduled_date': str(date.today()),
    })
    assert res.status_code == 201
    assert res.get_json()['status'] == 'pending'


def test_list_orders_by_status(client):
    res = client.get('/api/orders/?status=pending')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


# ── Allocation endpoints ──────────────────────────────────────────────────────

def test_run_allocation_empty(client):
    """Allocation with no data should return 200 with zero counts."""
    res = client.post('/api/allocation/run', json={'date': str(date.today())})
    assert res.status_code == 200
    data = res.get_json()
    assert 'metrics' in data


def test_allocation_runs_list(client):
    res = client.get('/api/allocation/runs')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_agent_summary_endpoint(client):
    res = client.get(f'/api/allocation/agent-summary?date={date.today()}')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_loads(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'DeliverIQ' in res.data


def test_dashboard_stats_api(client):
    res = client.get(f'/api/dashboard/stats?date={date.today()}')
    assert res.status_code == 200
    data = res.get_json()
    assert 'totals' in data
    assert 'tier_data' in data
    assert 'wh_summary' in data
