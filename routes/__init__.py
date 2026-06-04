from routes.admin import admin_bp
from routes.transfers import transfers_bp


def register_routes(app):
    app.register_blueprint(transfers_bp)
    app.register_blueprint(admin_bp)
