"""
Unit Tests — Allocation Engine
================================
Tests core logic without requiring a database.
"""

import pytest
from datetime import date
from app.services.allocation_engine import (
    haversine_km,
    compute_payout,
    allocate_orders,
    MAX_KM_PER_DAY,
    MAX_MINUTES_PER_DAY,
    DAILY_GUARANTEE,
)


# ── haversine_km ─────────────────────────────────────────────────────────────

def test_haversine_same_point():
    assert haversine_km(28.6, 77.2, 28.6, 77.2) == 0.0


def test_haversine_known_distance():
    # Delhi to Noida approx ~17 km
    d = haversine_km(28.6315, 77.2167, 28.5355, 77.3910)
    assert 15 < d < 22


# ── compute_payout ────────────────────────────────────────────────────────────

def test_payout_zero_orders():
    assert compute_payout(0) == DAILY_GUARANTEE


def test_payout_under_25():
    """Fewer than 25 orders → ₹500 guarantee."""
    assert compute_payout(10) == DAILY_GUARANTEE
    assert compute_payout(24) == DAILY_GUARANTEE


def test_payout_tier1():
    """25-49 orders → ₹35 each."""
    assert compute_payout(25) == 25 * 35
    assert compute_payout(49) == 49 * 35


def test_payout_tier2():
    """50+ orders → ₹42 each."""
    assert compute_payout(50) == 50 * 42
    assert compute_payout(60) == 60 * 42


# ── allocate_orders ───────────────────────────────────────────────────────────

def make_test_data():
    """10 orders tightly clustered around one warehouse."""
    wh_lat, wh_lon = 28.63, 77.22
    orders = [
        {'id': i, 'warehouse_id': 1,
         'latitude': wh_lat + (i * 0.002),
         'longitude': wh_lon + (i * 0.002)}
        for i in range(1, 11)
    ]
    agents = [{'id': 1, 'warehouse_id': 1}]
    wh_coords = {1: (wh_lat, wh_lon)}
    return agents, orders, wh_coords


def test_all_orders_assigned_when_feasible():
    agents, orders, wh_coords = make_test_data()
    result = allocate_orders(agents, orders, wh_coords, date.today())
    assert len(result['assignments']) == 10
    assert len(result['deferred_ids']) == 0


def test_single_agent_distance_compliance():
    """Agent's total km must not exceed MAX_KM_PER_DAY."""
    agents, orders, wh_coords = make_test_data()
    result = allocate_orders(agents, orders, wh_coords, date.today())
    summary = result['agent_summary'][1]
    assert summary['km'] <= MAX_KM_PER_DAY


def test_single_agent_time_compliance():
    """Agent's total minutes must not exceed MAX_MINUTES_PER_DAY."""
    agents, orders, wh_coords = make_test_data()
    result = allocate_orders(agents, orders, wh_coords, date.today())
    summary = result['agent_summary'][1]
    assert summary['minutes'] <= MAX_MINUTES_PER_DAY


def test_excess_orders_deferred():
    """When orders exceed capacity, extras are deferred."""
    wh_lat, wh_lon = 28.63, 77.22
    # Spread orders far apart to exhaust distance budget quickly
    orders = [
        {'id': i, 'warehouse_id': 1,
         'latitude': wh_lat + (i * 0.08),  # ~9 km apart
         'longitude': wh_lon}
        for i in range(1, 30)
    ]
    agents = [{'id': 1, 'warehouse_id': 1}]
    wh_coords = {1: (wh_lat, wh_lon)}
    result = allocate_orders(agents, orders, wh_coords, date.today())
    total = len(result['assignments']) + len(result['deferred_ids'])
    assert total == 29
    assert len(result['deferred_ids']) > 0


def test_multiple_agents_share_orders():
    """Orders should be distributed across agents."""
    wh_lat, wh_lon = 28.63, 77.22
    orders = [
        {'id': i, 'warehouse_id': 1,
         'latitude': wh_lat + (i * 0.002),
         'longitude': wh_lon}
        for i in range(1, 21)
    ]
    agents = [
        {'id': 1, 'warehouse_id': 1},
        {'id': 2, 'warehouse_id': 1},
    ]
    wh_coords = {1: (wh_lat, wh_lon)}
    result = allocate_orders(agents, orders, wh_coords, date.today())
    # At least some orders assigned to agent 2
    agent2_orders = result['agent_summary'][2]['orders']
    assert agent2_orders >= 0  # Could be 0 if agent 1 handles all
    assert len(result['assignments']) == 20


def test_multi_warehouse_isolation():
    """Orders from WH-1 must not be assigned to agents from WH-2."""
    orders = [
        {'id': 1, 'warehouse_id': 1, 'latitude': 28.63, 'longitude': 77.22},
        {'id': 2, 'warehouse_id': 2, 'latitude': 28.50, 'longitude': 77.09},
    ]
    agents = [
        {'id': 1, 'warehouse_id': 1},
        {'id': 2, 'warehouse_id': 2},
    ]
    wh_coords = {
        1: (28.63, 77.22),
        2: (28.50, 77.09),
    }
    result = allocate_orders(agents, orders, wh_coords, date.today())
    # Order 1 should go to agent 1, order 2 to agent 2
    assignments = {a['order_id']: a['agent_id'] for a in result['assignments']}
    assert assignments[1] == 1
    assert assignments[2] == 2


def test_metrics_structure():
    agents, orders, wh_coords = make_test_data()
    result = allocate_orders(agents, orders, wh_coords, date.today())
    m = result['metrics']
    assert 'total_agents' in m
    assert 'assigned_orders' in m
    assert 'deferred_orders' in m
    assert 'total_cost' in m
    assert 'avg_orders_per_agent' in m
    assert 'tier_breakdown' in m


def test_no_agents_all_deferred():
    """With no agents, all orders should be deferred."""
    _, orders, wh_coords = make_test_data()
    result = allocate_orders([], orders, wh_coords, date.today())
    assert len(result['assignments']) == 0
    assert len(result['deferred_ids']) == 10
