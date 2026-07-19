"""
RetailMind AI - Utility Functions & Decorators
"""
import os
import logging
from functools import wraps
from datetime import datetime
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from models import db, ActivityLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('retailmind')


def log_activity(action, details=''):
    """Log user activity to database."""
    try:
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                from models import User
                user = User.query.filter_by(username=identity).first()
                if user:
                    user_id = user.id
        except Exception:
            pass
        
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f'Failed to log activity: {str(e)}')
        db.session.rollback()


def admin_required(fn):
    """Decorator to require admin authentication."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identity = get_jwt_identity()
        if not identity:
            return jsonify({'error': 'Unauthorized'}), 401
        return fn(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file, subfolder=''):
    """Save uploaded file and return relative path."""
    if file and allowed_file(file.filename):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        
        upload_dir = current_app.config['UPLOAD_FOLDER']
        if subfolder:
            upload_dir = os.path.join(upload_dir, subfolder)
        
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        return f"/uploads/{subfolder}/{filename}" if subfolder else f"/uploads/{filename}"
    return None


def format_datetime(dt):
    """Format datetime for JSON response."""
    if dt is None:
        return None
    return dt.isoformat()


def parse_date(date_str):
    """Parse date string in various formats."""
    if not date_str:
        return None
    
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None
