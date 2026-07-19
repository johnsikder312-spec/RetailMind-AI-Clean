"""
RetailMind AI - Offer Routes
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from models import db, Offer, Product, User, Announcement
from utils import admin_required, log_activity, parse_date

offers_bp = Blueprint('offers', __name__, url_prefix='/api/offers')


@offers_bp.route('', methods=['GET'])
@admin_required
def get_offers():
    """Get all offers with optional filtering."""
    status = request.args.get('status', 'all')  # all, active, expired
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Offer.query
    
    now = datetime.utcnow()
    if status == 'active':
        query = query.filter(Offer.is_active == True).filter(
            (Offer.end_date == None) | (Offer.end_date > now)
        )
    elif status == 'expired':
        query = query.filter(
            (Offer.is_active == False) | (Offer.end_date <= now)
        )
    
    offers = query.order_by(Offer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'offers': [o.to_dict() for o in offers.items],
        'total': offers.total,
        'pages': offers.pages,
        'current_page': page
    }), 200


@offers_bp.route('/<int:offer_id>', methods=['GET'])
@admin_required
def get_offer(offer_id):
    """Get single offer by ID."""
    offer = Offer.query.get_or_404(offer_id)
    return jsonify({'offer': offer.to_dict()}), 200


@offers_bp.route('', methods=['POST'])
@admin_required
def create_offer():
    """Create a new offer."""
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Offer title is required'}), 400
    
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    
    offer = Offer(
        product_id=data.get('product_id'),
        title=data['title'].strip(),
        description=data.get('description', ''),
        announcement_text=data.get('announcement_text', ''),
        discount_percent=float(data.get('discount_percent', 0)),
        start_date=parse_date(data.get('start_date')) or datetime.utcnow(),
        end_date=parse_date(data.get('end_date')),
        is_active=data.get('is_active', True),
        language=data.get('language', 'english'),
        created_by=user.id if user else None
    )
    
    db.session.add(offer)
    db.session.commit()
    
    # Update product discount if linked
    if offer.product_id:
        product = Product.query.get(offer.product_id)
        if product:
            product.discount = offer.discount_percent
            product.final_price = product.price - (product.price * offer.discount_percent / 100)
            db.session.commit()
    
    # Auto-create announcement with TTS audio if announcement_text is provided
    announcement_data = None
    if offer.announcement_text and offer.announcement_text.strip():
        announcement_data = _create_announcement_with_tts(offer)
    
    log_activity('OFFER_CREATED', f'Offer "{offer.title}" created')
    
    response = {'offer': offer.to_dict(), 'message': 'Offer created successfully'}
    if announcement_data:
        response['announcement'] = announcement_data
        response['message'] = 'Offer and announcement created successfully'
    
    return jsonify(response), 201


def _create_announcement_with_tts(offer):
    """Create an Announcement record with TTS audio for an offer."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from tts.engine import generate_speech, get_audio_url
        
        # Pass the full language name — generate_speech handles the mapping internally
        audio_path = generate_speech(offer.announcement_text, offer.language or 'english')
        
        if not audio_path:
            logger.warning(f'TTS generation failed for offer "{offer.title}"')
            # Still create the announcement without audio
            audio_path = ''
        
        # Create Announcement record
        announcement = Announcement(
            offer_id=offer.id,
            audio_file_path=audio_path,
            language=offer.language or 'english',
            scheduled_interval=30,
            is_active=True
        )
        db.session.add(announcement)
        db.session.commit()
        
        logger.info(f'Announcement #{announcement.id} created for offer "{offer.title}"')
        log_activity('ANNOUNCEMENT_CREATED', f'Announcement created for offer "{offer.title}"')
        
        return announcement.to_dict()
        
    except Exception as e:
        logger.error(f'Failed to create announcement for offer "{offer.title}": {str(e)}')
        return None


@offers_bp.route('/<int:offer_id>', methods=['PUT'])
@admin_required
def update_offer(offer_id):
    """Update an existing offer."""
    offer = Offer.query.get_or_404(offer_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'title' in data:
        offer.title = data['title'].strip()
    if 'description' in data:
        offer.description = data['description']
    if 'announcement_text' in data:
        offer.announcement_text = data['announcement_text']
    if 'discount_percent' in data:
        offer.discount_percent = float(data['discount_percent'])
    if 'start_date' in data:
        offer.start_date = parse_date(data['start_date'])
    if 'end_date' in data:
        offer.end_date = parse_date(data['end_date'])
    if 'is_active' in data:
        offer.is_active = data['is_active']
    if 'language' in data:
        offer.language = data['language']
    if 'product_id' in data:
        offer.product_id = data['product_id']
    
    db.session.commit()
    
    # Update product discount if linked
    if offer.product_id:
        product = Product.query.get(offer.product_id)
        if product and 'discount_percent' in data:
            product.discount = offer.discount_percent
            product.final_price = product.price - (product.price * offer.discount_percent / 100)
            db.session.commit()
    
    log_activity('OFFER_UPDATED', f'Offer "{offer.title}" updated')
    
    return jsonify({'offer': offer.to_dict(), 'message': 'Offer updated successfully'}), 200


@offers_bp.route('/<int:offer_id>', methods=['DELETE'])
@admin_required
def delete_offer(offer_id):
    """Delete an offer."""
    offer = Offer.query.get_or_404(offer_id)
    title = offer.title
    
    db.session.delete(offer)
    db.session.commit()
    
    log_activity('OFFER_DELETED', f'Offer "{title}" deleted')
    
    return jsonify({'message': f'Offer "{title}" deleted successfully'}), 200


@offers_bp.route('/<int:offer_id>/toggle', methods=['POST'])
@admin_required
def toggle_offer(offer_id):
    """Toggle offer active status."""
    offer = Offer.query.get_or_404(offer_id)
    offer.is_active = not offer.is_active
    db.session.commit()
    
    status = 'activated' if offer.is_active else 'deactivated'
    log_activity('OFFER_TOGGLED', f'Offer "{offer.title}" {status}')
    
    return jsonify({
        'offer': offer.to_dict(),
        'message': f'Offer {status}'
    }), 200
