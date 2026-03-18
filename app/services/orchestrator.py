"""
Allocation Orchestrator
========================
Ties the DB layer to the allocation engine.
Called by the cron scheduler or manually via API.
"""

from datetime import date, timedelta
from app.extensions import db
from app.models import (
    Agent, AgentCheckin, Order, Assignment, Warehouse, AllocationRun
)
from app.services.allocation_engine import allocate_orders


def run_daily_allocation(target_date: date = None) -> dict:
    """
    Full daily allocation job:
      1. Pull checked-in agents for target_date
      2. Pull pending + deferred orders for target_date
      3. Run allocation engine
      4. Persist assignments
      5. Mark deferred orders
      6. Record AllocationRun summary
    """
    if target_date is None:
        target_date = date.today()

    # ── 1. Checked-in agents ─────────────────────────────────────────────────
    checked_in = (
        db.session.query(Agent)
        .join(AgentCheckin, AgentCheckin.agent_id == Agent.id)
        .filter(
            AgentCheckin.checkin_date == target_date,
            AgentCheckin.is_available == True,
            Agent.is_active == True,
        )
        .all()
    )

    agents_data = [{'id': a.id, 'warehouse_id': a.warehouse_id} for a in checked_in]

    # ── 2. Pending orders (today's + deferred from prior days) ───────────────
    orders_qs = Order.query.filter(
        Order.status.in_(['pending', 'deferred']),
        Order.scheduled_date <= target_date,
    ).all()

    orders_data = [
        {
            'id': o.id,
            'warehouse_id': o.warehouse_id,
            'latitude': o.latitude,
            'longitude': o.longitude,
        }
        for o in orders_qs
    ]

    # ── 3. Warehouse coordinates ─────────────────────────────────────────────
    warehouses = Warehouse.query.all()
    wh_coords = {wh.id: (wh.latitude, wh.longitude) for wh in warehouses}

    # ── 4. Run allocation engine ─────────────────────────────────────────────
    result = allocate_orders(agents_data, orders_data, wh_coords, target_date)

    # ── 5. Persist assignments ────────────────────────────────────────────────
    assigned_order_ids = set()
    for a in result['assignments']:
        assignment = Assignment(
            agent_id=a['agent_id'],
            order_id=a['order_id'],
            assignment_date=target_date,
            distance_km=a['distance_km'],
            estimated_minutes=a['estimated_minutes'],
            sequence=a['sequence'],
        )
        db.session.add(assignment)
        assigned_order_ids.add(a['order_id'])

    # Update order statuses
    for order in orders_qs:
        if order.id in assigned_order_ids:
            order.status = 'assigned'
        else:
            order.status = 'deferred'
            order.deferred_count += 1
            order.scheduled_date = target_date + timedelta(days=1)

    # ── 6. Record AllocationRun ───────────────────────────────────────────────
    metrics = result['metrics']
    run = AllocationRun(
        run_date=target_date,
        total_agents=metrics['total_agents'],
        total_orders=metrics['total_orders'],
        assigned_orders=metrics['assigned_orders'],
        deferred_orders=metrics['deferred_orders'],
        total_cost=metrics['total_cost'],
        avg_orders_per_agent=metrics['avg_orders_per_agent'],
        avg_km_per_agent=metrics['avg_km_per_agent'],
        status='completed',
    )
    db.session.add(run)
    db.session.commit()

    return {
        'run_id': run.id,
        'metrics': metrics,
        'agent_summary': result['agent_summary'],
    }
