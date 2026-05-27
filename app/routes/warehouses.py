from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Warehouse

warehouses_bp = Blueprint('warehouses', __name__)


@warehouses_bp.route('/', methods=['GET'])
def list_warehouses():
    warehouses = Warehouse.query.all()
    return jsonify([w.to_dict() for w in warehouses])


@warehouses_bp.route('/<int:wid>', methods=['GET'])
def get_warehouse(wid):
    wh = Warehouse.query.get_or_404(wid)
    return jsonify(wh.to_dict())


@warehouses_bp.route('/', methods=['POST'])
def create_warehouse():
    data = request.get_json()
    wh = Warehouse(
        name=data['name'],
        city=data.get('city', 'Delhi'),
        latitude=data['latitude'],
        longitude=data['longitude'],
    )
    db.session.add(wh)
    db.session.commit()
    return jsonify(wh.to_dict()), 201
