"""
RetailMind AI - Category Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from models import db, Category
from utils import admin_required, log_activity

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')


@categories_bp.route('', methods=['GET'])
@admin_required
def get_categories():
    """Get all categories."""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({'categories': [c.to_dict() for c in categories]}), 200


@categories_bp.route('', methods=['POST'])
@admin_required
def create_category():
    """Create a new category."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400
    
    existing = Category.query.filter_by(name=data['name'].strip()).first()
    if existing:
        return jsonify({'error': 'Category already exists'}), 400
    
    category = Category(
        name=data['name'].strip(),
        description=data.get('description', '')
    )
    
    db.session.add(category)
    db.session.commit()
    
    log_activity('CATEGORY_CREATED', f'Category "{category.name}" created')
    
    return jsonify({'category': category.to_dict(), 'message': 'Category created'}), 201


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    """Update a category."""
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        category.name = data['name'].strip()
    if 'description' in data:
        category.description = data['description']
    
    db.session.commit()
    
    log_activity('CATEGORY_UPDATED', f'Category "{category.name}" updated')
    
    return jsonify({'category': category.to_dict(), 'message': 'Category updated'}), 200


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """Delete a category."""
    category = Category.query.get_or_404(category_id)
    name = category.name
    
    db.session.delete(category)
    db.session.commit()
    
    log_activity('CATEGORY_DELETED', f'Category "{name}" deleted')
    
    return jsonify({'message': f'Category "{name}" deleted'}), 200
