import os
from flask import Flask
from .extensions import db
from .scheduler import init_scheduler


def create_app(config=None):
    app = Flask(__name__)

    # Default config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///delivery_system.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    if config:
        app.config.update(config)

    db.init_app(app)

    # Register blueprints
    from .routes.warehouses import warehouses_bp
    from .routes.agents import agents_bp
    from .routes.orders import orders_bp
    from .routes.allocation import allocation_bp
    from .routes.dashboard import dashboard_bp

    app.register_blueprint(warehouses_bp, url_prefix='/api/warehouses')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(allocation_bp, url_prefix='/api/allocation')
    app.register_blueprint(dashboard_bp)

    # Start scheduler
    init_scheduler(app)

    return app
