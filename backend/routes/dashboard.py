"""
RetailMind AI - Dashboard Routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from sqlalchemy import func

from models import db, Product, Offer, Announcement, ActivityLog, Category
from utils import admin_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """Get dashboard statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Product stats
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock_quantity < 10).count()
    
    # Offer stats
    active_offers = Offer.query.filter(
        Offer.is_active == True,
        (Offer.end_date == None) | (Offer.end_date > now)
    ).count()
    
    expired_offers = Offer.query.filter(
        (Offer.is_active == False) | (Offer.end_date <= now)
    ).count()
    
    # Announcement stats
    announcements_today = Announcement.query.filter(
        Announcement.last_played >= today_start
    ).count()
    
    total_announcements = Announcement.query.filter_by(is_active=True).count()
    
    # Recent activity
    recent_logs = ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(10).all()
    
    # Low stock products
    low_stock_items = Product.query.filter(
        Product.stock_quantity < 10
    ).order_by(Product.stock_quantity).limit(5).all()
    
    # Category distribution
    categories = Category.query.all()
    category_data = []
    for cat in categories:
        count = Product.query.filter_by(category_id=cat.id).count()
        if count > 0:
            category_data.append({'name': cat.name, 'count': count})
    
    # Monthly offer trends (last 6 months)
    monthly_trends = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=i*30)).replace(day=1, hour=0, minute=0, second=0)
        if i > 0:
            next_month = (now - timedelta(days=(i-1)*30)).replace(day=1)
            month_end = next_month
        else:
            month_end = now
        
        count = Offer.query.filter(
            Offer.created_at >= month_start,
            Offer.created_at <= month_end
        ).count()
        
        monthly_trends.append({
            'month': month_start.strftime('%b'),
            'offers': count
        })
    
    return jsonify({
        'stats': {
            'total_products': total_products,
            'active_offers': active_offers,
            'expired_offers': expired_offers,
            'low_stock_products': low_stock_products,
            'announcements_today': announcements_today,
            'active_announcements': total_announcements
        },
        'recent_activity': [log.to_dict() for log in recent_logs],
        'low_stock_items': [p.to_dict() for p in low_stock_items],
        'category_distribution': category_data,
        'monthly_trends': monthly_trends
    }), 200
