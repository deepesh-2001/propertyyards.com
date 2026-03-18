from flask import Blueprint, jsonify, request
from datetime import date
from app.extensions import db
from app.models import Order

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/', methods=['GET'])
def list_orders():
    status = request.args.get('status')
    date_str = request.args.get('date')
    wid = request.args.get('warehouse_id', type=int)

    q = Order.query
    if status:
        q = q.filter_by(status=status)
    if date_str:
        try:
            q = q.filter(Order.scheduled_date == date.fromisoformat(date_str))
        except ValueError:
            return jsonify({'error': 'Invalid date'}), 400
    if wid:
        q = q.filter_by(warehouse_id=wid)

    orders = q.limit(200).all()
    return jsonify([o.to_dict() for o in orders])


@orders_bp.route('/<int:oid>', methods=['GET'])
def get_order(oid):
    order = Order.query.get_or_404(oid)
    return jsonify(order.to_dict())


@orders_bp.route('/', methods=['POST'])
def create_order():
    data = request.get_json()
    order = Order(
        order_number=data['order_number'],
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone'),
        delivery_address=data.get('delivery_address'),
        latitude=data['latitude'],
        longitude=data['longitude'],
        warehouse_id=data['warehouse_id'],
        weight_kg=data.get('weight_kg', 1.0),
        status='pending',
        scheduled_date=date.fromisoformat(data.get('scheduled_date', str(date.today()))),
    )
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
