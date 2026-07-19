"""
RetailMind AI - Product Routes
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Product, Category, User
from utils import admin_required, log_activity, save_upload_file, parse_date

products_bp = Blueprint('products', __name__, url_prefix='/api/products')


@products_bp.route('', methods=['GET'])
@admin_required
def get_products():
    """Get all products with optional filtering."""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    low_stock = request.args.get('low_stock', type=bool)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Product.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            Product.name.ilike(f'%{search}%') |
            Product.brand.ilike(f'%{search}%')
        )
    
    if low_stock:
        query = query.filter(Product.stock_quantity < 10)
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'products': [p.to_dict() for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': page
    }), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    """Get single product by ID."""
    product = Product.query.get_or_404(product_id)
    return jsonify({'product': product.to_dict()}), 200


@products_bp.route('', methods=['POST'])
@admin_required
def create_product():
    """Create a new product."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Product name is required'}), 400
    
    price = float(data.get('price', 0))
    discount = float(data.get('discount', 0))
    final_price = price - (price * discount / 100)
    
    product = Product(
        name=data['name'].strip(),
        brand=data.get('brand', '').strip(),
        category_id=data.get('category_id'),
        price=price,
        discount=discount,
        final_price=final_price,
        stock_quantity=int(data.get('stock_quantity', 0)),
        image_url=data.get('image_url', '')
    )
    
    db.session.add(product)
    db.session.commit()
    
    identity = get_jwt_identity()
    log_activity('PRODUCT_CREATED', f'Product "{product.name}" created by {identity}')
    
    return jsonify({'product': product.to_dict(), 'message': 'Product created successfully'}), 201


@products_bp.route('/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    """Update an existing product."""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        product.name = data['name'].strip()
    if 'brand' in data:
        product.brand = data['brand'].strip()
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'price' in data:
        product.price = float(data['price'])
    if 'discount' in data:
        product.discount = float(data['discount'])
    if 'stock_quantity' in data:
        product.stock_quantity = int(data['stock_quantity'])
    if 'image_url' in data:
        product.image_url = data['image_url']
    
    # Recalculate final price
    product.final_price = product.price - (product.price * product.discount / 100)
    
    db.session.commit()
    
    log_activity('PRODUCT_UPDATED', f'Product "{product.name}" updated')
    
    return jsonify({'product': product.to_dict(), 'message': 'Product updated successfully'}), 200


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    """Delete a product."""
    product = Product.query.get_or_404(product_id)
    name = product.name
    
    db.session.delete(product)
    db.session.commit()
    
    log_activity('PRODUCT_DELETED', f'Product "{name}" deleted')
    
    return jsonify({'message': f'Product "{name}" deleted successfully'}), 200


@products_bp.route('/<int:product_id>/upload-image', methods=['POST'])
@admin_required
def upload_product_image(product_id):
    """Upload product image."""
    product = Product.query.get_or_404(product_id)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    image_url = save_upload_file(file, 'products')
    
    if not image_url:
        return jsonify({'error': 'Invalid file type'}), 400
    
    product.image_url = image_url
    db.session.commit()
    
    log_activity('IMAGE_UPLOADED', f'Image uploaded for product "{product.name}"')
    
    return jsonify({
        'product': product.to_dict(),
        'message': 'Image uploaded successfully'
    }), 200
