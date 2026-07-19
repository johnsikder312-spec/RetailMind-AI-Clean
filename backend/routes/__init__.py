"""
RetailMind AI - Routes Package
"""
from routes.auth import auth_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.offers import offers_bp
from routes.dashboard import dashboard_bp
from routes.ai_routes import ai_bp, chat_bp, intelligence_bp
from routes.ocr_routes import ocr_bp
from routes.tts_routes import tts_bp
from routes.reports import reports_bp


def register_routes(app):
    """Register all blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(reports_bp)
