from flask import Blueprint, jsonify, request
from datetime import date
from app.extensions import db
from app.models import AllocationRun, Assignment, Agent
from app.services.orchestrator import run_daily_allocation
from app.services.seed_data import seed_database

allocation_bp = Blueprint('allocation', __name__)


@allocation_bp.route('/run', methods=['POST'])
def trigger_allocation():
    """Manually trigger the allocation job for a given date."""
    data = request.get_json(silent=True) or {}
    target_date_str = data.get('date')

    try:
        target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    result = run_daily_allocation(target_date)
    return jsonify(result), 200


@allocation_bp.route('/seed', methods=['POST'])
def seed():
    """Seed the database with test data."""
    data = request.get_json(silent=True) or {}
    target_date_str = data.get('date')
    try:
        target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    result = seed_database(db, target_date)
    return jsonify(result), 200


@allocation_bp.route('/runs', methods=['GET'])
def list_runs():
    """List all allocation run summaries."""
    runs = AllocationRun.query.order_by(AllocationRun.run_date.desc()).limit(30).all()
    return jsonify([r.to_dict() for r in runs])


@allocation_bp.route('/runs/<int:run_id>', methods=['GET'])
def get_run(run_id):
    run = AllocationRun.query.get_or_404(run_id)
    return jsonify(run.to_dict())


@allocation_bp.route('/agent-summary', methods=['GET'])
def agent_summary():
    """Get per-agent assignment summary for a given date."""
    date_str = request.args.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    results = (
        db.session.query(
            Agent.id,
            Agent.name,
            Agent.warehouse_id,
            db.func.count(Assignment.id).label('order_count'),
            db.func.sum(Assignment.distance_km).label('total_km'),
            db.func.sum(Assignment.estimated_minutes).label('total_minutes'),
        )
        .outerjoin(Assignment, (Assignment.agent_id == Agent.id) &
                   (Assignment.assignment_date == target_date))
        .group_by(Agent.id)
        .all()
    )

    summary = []
    for r in results:
        n = r.order_count or 0
        if n >= 50:
            payout = n * 42
            tier = '₹42/order'
        elif n >= 25:
            payout = n * 35
            tier = '₹35/order'
        else:
            payout = 500 if n > 0 else 0
            tier = 'Guarantee' if n > 0 else 'Idle'

        summary.append({
            'agent_id': r.id,
            'agent_name': r.name,
            'warehouse_id': r.warehouse_id,
            'orders': n,
            'total_km': round(r.total_km or 0, 2),
            'total_minutes': round(r.total_minutes or 0, 1),
            'payout': payout,
            'tier': tier,
        })

    return jsonify(summary)
