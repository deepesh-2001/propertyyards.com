from flask import Blueprint, jsonify, request
from datetime import date
from app.extensions import db
from app.models import Agent, AgentCheckin

agents_bp = Blueprint('agents', __name__)


@agents_bp.route('/', methods=['GET'])
def list_agents():
    agents = Agent.query.filter_by(is_active=True).all()
    return jsonify([a.to_dict() for a in agents])


@agents_bp.route('/<int:aid>', methods=['GET'])
def get_agent(aid):
    agent = Agent.query.get_or_404(aid)
    return jsonify(agent.to_dict())


@agents_bp.route('/', methods=['POST'])
def create_agent():
    data = request.get_json()
    agent = Agent(
        name=data['name'],
        phone=data.get('phone'),
        warehouse_id=data['warehouse_id'],
    )
    db.session.add(agent)
    db.session.commit()
    return jsonify(agent.to_dict()), 201


@agents_bp.route('/<int:aid>/checkin', methods=['POST'])
def checkin_agent(aid):
    agent = Agent.query.get_or_404(aid)
    today = date.today()
    existing = AgentCheckin.query.filter_by(agent_id=aid, checkin_date=today).first()
    if existing:
        return jsonify({'message': 'Already checked in', 'checkin': existing.to_dict()})

    checkin = AgentCheckin(agent_id=aid, checkin_date=today, is_available=True)
    db.session.add(checkin)
    db.session.commit()
    return jsonify({'message': 'Checked in', 'checkin': checkin.to_dict()}), 201
