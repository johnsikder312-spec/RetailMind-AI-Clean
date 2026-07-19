"""
RetailMind AI - AI Routes (Offer Generator, Chatbot, Intelligence)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from models import db, Offer, Product, Category, ChatMessage, User
from utils import admin_required, log_activity, parse_date
from ai.offer_generator import generate_offer_from_text, generate_multilingual_announcement
from ai.chatbot import process_chat_message
from ai.intelligence import get_business_recommendations

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
intelligence_bp = Blueprint('intelligence', __name__, url_prefix='/api/intelligence')


# ===================== AI OFFER GENERATOR =====================

@ai_bp.route('/generate-offer', methods=['POST'])
@admin_required
def generate_offer():
    """Generate an offer from natural language input using AI."""
    data = request.get_json()
    
    if not data or not data.get('input_text'):
        return jsonify({'error': 'Input text is required'}), 400
    
    input_text = data['input_text'].strip()
    language = data.get('language', 'english')
    
    result = generate_offer_from_text(input_text, language)
    
    if result is None:
        return jsonify({'error': 'Failed to generate offer'}), 500
    
    log_activity('AI_OFFER_GENERATED', f'AI generated offer from: "{input_text}"')
    
    return jsonify({
        'offer_data': result,
        'message': 'Offer generated successfully. Review and edit before saving.'
    }), 200


@ai_bp.route('/translate-announcement', methods=['POST'])
@admin_required
def translate_announcement():
    """Translate an announcement to another language."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    offer_data = data.get('offer_data', {})
    target_language = data.get('language', 'english')
    
    translated = generate_multilingual_announcement(offer_data, target_language)
    
    return jsonify({
        'announcement_text': translated,
        'language': target_language
    }), 200


# ===================== AI CHATBOT =====================

@chat_bp.route('/message', methods=['POST'])
@admin_required
def send_message():
    """Send a message to the AI chatbot."""
    data = request.get_json()
    
    if not data or not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400
    
    message = data['message'].strip()
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    
    # Save user message
    user_msg = ChatMessage(
        user_id=user.id if user else None,
        role='user',
        content=message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Get AI response
    response_text = process_chat_message(message, user.id if user else None)
    
    # Save assistant message
    assistant_msg = ChatMessage(
        user_id=user.id if user else None,
        role='assistant',
        content=response_text
    )
    db.session.add(assistant_msg)
    db.session.commit()
    
    return jsonify({
        'response': response_text,
        'message_id': assistant_msg.id
    }), 200


@chat_bp.route('/history', methods=['GET'])
@admin_required
def get_chat_history():
    """Get chat message history."""
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = ChatMessage.query
    if user:
        query = query.filter_by(user_id=user.id)
    
    messages = query.order_by(ChatMessage.timestamp.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'messages': [m.to_dict() for m in messages.items],
        'total': messages.total
    }), 200


@chat_bp.route('/clear', methods=['POST'])
@admin_required
def clear_chat():
    """Clear chat history."""
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    
    if user:
        ChatMessage.query.filter_by(user_id=user.id).delete()
        db.session.commit()
    
    return jsonify({'message': 'Chat history cleared'}), 200


# ===================== BUSINESS INTELLIGENCE =====================

@intelligence_bp.route('/recommendations', methods=['GET'])
@admin_required
def get_recommendations():
    """Get AI-powered business recommendations."""
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    recommendations = get_business_recommendations(force_refresh=force_refresh)
    
    return jsonify(recommendations), 200
