"""
RetailMind AI - Main Application Entry Point
=============================================
A modern AI-powered retail promotion assistant.
"""
import os
import sys

# Fix Windows console encoding (must be before any imports that may print Unicode)
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

from config import Config
from models import db
from services.scheduler import init_scheduler, shutdown_scheduler


def _auto_migrate(app):
    """Add missing columns to existing tables (safe for SQLite)."""
    import sqlite3
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing columns for announcements table
        cursor.execute('PRAGMA table_info(announcements)')
        cols = [row[1] for row in cursor.fetchall()]
        
        migrations = [
            ('language', "ALTER TABLE announcements ADD COLUMN language VARCHAR(20) DEFAULT 'english'"),
            ('background_music', "ALTER TABLE announcements ADD COLUMN background_music VARCHAR(100) DEFAULT ''"),
            ('music_volume', "ALTER TABLE announcements ADD COLUMN music_volume INTEGER DEFAULT 15"),
        ]
        
        for col_name, sql in migrations:
            if col_name not in cols:
                cursor.execute(sql)
                print(f'[Migration] Added {col_name} column to announcements table')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'[Migration] Warning: {e}')


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
    
    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    JWTManager(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.categories import categories_bp
    from routes.offers import offers_bp
    from routes.dashboard import dashboard_bp
    from routes.ai_routes import ai_bp, chat_bp, intelligence_bp
    from routes.ocr_routes import ocr_bp
    from routes.tts_routes import tts_bp
    from routes.reports import reports_bp
    
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
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/audio/<path:filename>')
    def serve_audio(filename):
        return send_from_directory(app.config['AUDIO_FOLDER'], filename)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'RetailMind AI',
            'version': '1.0.0'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'error': 'Method not allowed'}), 405
    
    # Initialize database and seed
    with app.app_context():
        db.create_all()
        # Auto-migrate: add columns that may be missing from older databases
        _auto_migrate(app)
        from database.seed import seed_database
        seed_database(app)
    
    # Initialize scheduler
    init_scheduler(app)
    
    # Initialize OCR reader eagerly (loads model on startup)
    from ocr.scanner import init_ocr_reader
    init_ocr_reader()
    
    # Shutdown scheduler on app exit
    import atexit
    atexit.register(shutdown_scheduler)
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("\n" + "=" * 50)
    print("  RetailMind AI - Backend Server")
    print("  Running on: http://localhost:5000")
    print("  API Docs:   http://localhost:5000/api/health")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
