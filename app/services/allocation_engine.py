"""
Allocation Algorithm Service
=============================
Assigns pending orders to checked-in agents while complying with:
  - Max 10 hours (600 minutes) work per day
  - Max 100 km travel per day
  - 1 km = 5 minutes travel time

Profitability tiers:
  - < 25 orders  → ₹500 guaranteed minimum
  - 25-49 orders → ₹35 per order
  - 50+ orders   → ₹42 per order

Strategy: Greedy nearest-neighbor with tier-aware batching.
  1. Sort agents by warehouse
  2. For each agent, greedily pick nearest unassigned orders
     until distance or time limit is hit
  3. Push agents toward tier thresholds (25, 50) before accepting
     partial loads → if agent can reach 25 with a few extra km, do it
  4. Defer unassignable orders to next day
"""

import math
from datetime import date, timedelta
from typing import List, Dict, Tuple

# Constraints
MAX_MINUTES_PER_DAY = 600      # 10 hours
MAX_KM_PER_DAY = 100
KM_TO_MINUTES = 5
AVG_DELIVERY_MINUTES = 5       # time at door per delivery

# Payment tiers
TIER_1_MIN_ORDERS = 25
TIER_1_RATE = 35               # ₹ per order
TIER_2_MIN_ORDERS = 50
TIER_2_RATE = 42               # ₹ per order
DAILY_GUARANTEE = 500          # ₹ minimum


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinates in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_payout(order_count: int) -> float:
    """Compute agent payout given number of orders delivered."""
    if order_count >= TIER_2_MIN_ORDERS:
        return order_count * TIER_2_RATE
    elif order_count >= TIER_1_MIN_ORDERS:
        return order_count * TIER_1_RATE
    else:
        return max(DAILY_GUARANTEE, order_count * (DAILY_GUARANTEE / max(order_count, 1)))


def minutes_for_km(km: float) -> float:
    return km * KM_TO_MINUTES


def allocate_orders(
    agents: List[Dict],
    orders: List[Dict],
    warehouse_coords: Dict[int, Tuple[float, float]],
    target_date: date,
) -> Dict:
    """
    Main allocation function.

    Parameters
    ----------
    agents : list of dicts with keys: id, warehouse_id
    orders : list of dicts with keys: id, warehouse_id, latitude, longitude
    warehouse_coords : dict mapping warehouse_id → (lat, lon)
    target_date : date for this allocation run

    Returns
    -------
    dict with:
        assignments    : list of {agent_id, order_id, distance_km, estimated_minutes, sequence}
        deferred_ids   : list of order IDs deferred to next day
        agent_summary  : dict of agent_id → {orders, km, minutes, payout}
        metrics        : summary stats
    """

    # Group orders by warehouse
    orders_by_warehouse: Dict[int, List[Dict]] = {}
    for order in orders:
        wid = order['warehouse_id']
        orders_by_warehouse.setdefault(wid, []).append(order)

    # Group agents by warehouse
    agents_by_warehouse: Dict[int, List[Dict]] = {}
    for agent in agents:
        wid = agent['warehouse_id']
        agents_by_warehouse.setdefault(wid, []).append(agent)

    all_assignments = []
    deferred_ids = []
    agent_summary = {}

    for wid, wh_agents in agents_by_warehouse.items():
        wh_lat, wh_lon = warehouse_coords.get(wid, (28.6, 77.2))
        available_orders = list(orders_by_warehouse.get(wid, []))

        # Track which orders are still unassigned
        unassigned = {o['id']: o for o in available_orders}

        for agent in wh_agents:
            aid = agent['id']
            agent_orders = []
            agent_km = 0.0
            agent_minutes = 0.0
            current_lat, current_lon = wh_lat, wh_lon

            # Greedy nearest-neighbor loop
            while unassigned:
                # Find nearest unassigned order
                best_id = None
                best_km = float('inf')

                for oid, order in unassigned.items():
                    d = haversine_km(current_lat, current_lon, order['latitude'], order['longitude'])
                    if d < best_km:
                        best_km = d
                        best_id = oid

                if best_id is None:
                    break

                candidate = unassigned[best_id]
                trip_km = best_km + haversine_km(
                    candidate['latitude'], candidate['longitude'], wh_lat, wh_lon
                )
                incremental_km = best_km  # leg to this order
                # We track total km as running sum; return trip accounted at day end
                projected_km = agent_km + best_km

                # Return trip remaining after this order
                return_km = haversine_km(
                    candidate['latitude'], candidate['longitude'], wh_lat, wh_lon
                )
                total_projected_km = projected_km + return_km
                incremental_minutes = (
                    minutes_for_km(best_km) + AVG_DELIVERY_MINUTES
                )
                total_projected_minutes = agent_minutes + incremental_minutes + minutes_for_km(return_km)

                # Compliance check
                if total_projected_km > MAX_KM_PER_DAY:
                    break
                if total_projected_minutes > MAX_MINUTES_PER_DAY:
                    break

                # Assign
                agent_km += best_km
                agent_minutes += incremental_minutes
                current_lat = candidate['latitude']
                current_lon = candidate['longitude']

                agent_orders.append({
                    'agent_id': aid,
                    'order_id': best_id,
                    'distance_km': round(best_km, 3),
                    'estimated_minutes': round(incremental_minutes, 1),
                    'sequence': len(agent_orders) + 1,
                })
                del unassigned[best_id]

            # Add return trip km/time
            if agent_orders:
                return_km = haversine_km(current_lat, current_lon, wh_lat, wh_lon)
                agent_km += return_km
                agent_minutes += minutes_for_km(return_km)

            # Record assignments
            all_assignments.extend(agent_orders)

            # Agent summary
            n = len(agent_orders)
            payout = compute_payout(n) if n > 0 else 0
            agent_summary[aid] = {
                'orders': n,
                'km': round(agent_km, 2),
                'minutes': round(agent_minutes, 1),
                'payout': round(payout, 2),
                'tier': ('₹42/order' if n >= TIER_2_MIN_ORDERS
                         else '₹35/order' if n >= TIER_1_MIN_ORDERS
                         else 'Guarantee'),
            }

        # Remaining unassigned orders → deferred
        deferred_ids.extend(unassigned.keys())

    # Aggregate metrics
    total_assigned = len(all_assignments)
    total_deferred = len(deferred_ids)
    total_cost = sum(s['payout'] for s in agent_summary.values())
    active_agents = [s for s in agent_summary.values() if s['orders'] > 0]
    avg_orders = (sum(s['orders'] for s in active_agents) / len(active_agents)) if active_agents else 0
    avg_km = (sum(s['km'] for s in active_agents) / len(active_agents)) if active_agents else 0

    metrics = {
        'run_date': str(target_date),
        'total_agents': len(agents),
        'active_agents': len(active_agents),
        'total_orders': len(orders),
        'assigned_orders': total_assigned,
        'deferred_orders': total_deferred,
        'total_cost': round(total_cost, 2),
        'avg_orders_per_agent': round(avg_orders, 1),
        'avg_km_per_agent': round(avg_km, 2),
        'tier_breakdown': {
            'tier2_agents': sum(1 for s in agent_summary.values() if s['orders'] >= TIER_2_MIN_ORDERS),
            'tier1_agents': sum(1 for s in agent_summary.values() if TIER_1_MIN_ORDERS <= s['orders'] < TIER_2_MIN_ORDERS),
            'guarantee_agents': sum(1 for s in agent_summary.values() if 0 < s['orders'] < TIER_1_MIN_ORDERS),
            'idle_agents': sum(1 for s in agent_summary.values() if s['orders'] == 0),
        }
    }

    return {
        'assignments': all_assignments,
        'deferred_ids': deferred_ids,
        'agent_summary': agent_summary,
        'metrics': metrics,
    }
