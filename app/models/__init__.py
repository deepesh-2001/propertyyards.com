from datetime import datetime
from app.extensions import db


class Warehouse(db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), default='Delhi')
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    agents = db.relationship('Agent', backref='warehouse', lazy=True)
    orders = db.relationship('Order', backref='warehouse', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }


class Agent(db.Model):
    __tablename__ = 'agents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    checkins = db.relationship('AgentCheckin', backref='agent', lazy=True)
    assignments = db.relationship('Assignment', backref='agent', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'warehouse_id': self.warehouse_id,
            'is_active': self.is_active,
        }


class AgentCheckin(db.Model):
    __tablename__ = 'agent_checkins'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    checkin_date = db.Column(db.Date, nullable=False)
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('agent_id', 'checkin_date', name='uq_agent_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'checkin_date': str(self.checkin_date),
            'checkin_time': str(self.checkin_time),
            'is_available': self.is_available,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(15))
    delivery_address = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    weight_kg = db.Column(db.Float, default=1.0)

    # Status: pending, assigned, delivered, deferred
    status = db.Column(db.String(20), default='pending')
    scheduled_date = db.Column(db.Date, nullable=False)
    deferred_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignment = db.relationship('Assignment', backref='order', uselist=False, lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'delivery_address': self.delivery_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'warehouse_id': self.warehouse_id,
            'status': self.status,
            'scheduled_date': str(self.scheduled_date),
            'deferred_count': self.deferred_count,
        }


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    assignment_date = db.Column(db.Date, nullable=False)
    distance_km = db.Column(db.Float)
    estimated_minutes = db.Column(db.Float)
    sequence = db.Column(db.Integer)  # delivery order in route
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'order_id': self.order_id,
            'assignment_date': str(self.assignment_date),
            'distance_km': self.distance_km,
            'estimated_minutes': self.estimated_minutes,
            'sequence': self.sequence,
        }


class AllocationRun(db.Model):
    __tablename__ = 'allocation_runs'

    id = db.Column(db.Integer, primary_key=True)
    run_date = db.Column(db.Date, nullable=False)
    run_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_agents = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    assigned_orders = db.Column(db.Integer, default=0)
    deferred_orders = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    avg_orders_per_agent = db.Column(db.Float, default=0.0)
    avg_km_per_agent = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='completed')

    def to_dict(self):
        return {
            'id': self.id,
            'run_date': str(self.run_date),
            'run_time': str(self.run_time),
            'total_agents': self.total_agents,
            'total_orders': self.total_orders,
            'assigned_orders': self.assigned_orders,
            'deferred_orders': self.deferred_orders,
            'total_cost': self.total_cost,
            'avg_orders_per_agent': self.avg_orders_per_agent,
            'avg_km_per_agent': self.avg_km_per_agent,
            'status': self.status,
        }
