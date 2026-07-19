"""
RetailMind AI - AI Chatbot using Google Gemini
"""
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_store_context():
    """Get current store data context for the chatbot."""
    from models import db, Product, Offer, Category
    
    now = datetime.utcnow()
    
    # Active offers
    active_offers = Offer.query.filter(
        Offer.is_active == True,
        (Offer.end_date == None) | (Offer.end_date > now)
    ).all()
    
    # Low stock products
    low_stock = Product.query.filter(Product.stock_quantity < 10).order_by(
        Product.stock_quantity
    ).limit(10).all()
    
    # Total products
    total_products = Product.query.count()
    
    # Categories
    categories = Category.query.all()
    
    # Products expiring soon (offers ending in next 3 days)
    expiring_soon = Offer.query.filter(
        Offer.is_active == True,
        Offer.end_date > now,
        Offer.end_date <= datetime.utcnow() + __import__('datetime').timedelta(days=3)
    ).all()
    
    context = f"""
Store Database Summary (as of {now.strftime('%Y-%m-%d %H:%M')}):

Total Products: {total_products}
Total Categories: {len(categories)}
Active Offers: {len(active_offers)}
Low Stock Products (< 10 units): {len(low_stock)}
Offers Expiring in 3 days: {len(expiring_soon)}

Active Offers:
{chr(10).join([f"- {o.title} ({o.discount_percent}% off, ends {o.end_date.strftime('%Y-%m-%d') if o.end_date else 'N/A'})" for o in active_offers[:10]]) or 'None'}

Low Stock Products:
{chr(10).join([f"- {p.name}: {p.stock_quantity} units (Price: ₹{p.price})" for p in low_stock]) or 'None'}

Expiring Soon:
{chr(10).join([f"- {o.title} (expires {o.end_date.strftime('%Y-%m-%d') if o.end_date else 'N/A'})" for o in expiring_soon[:5]]) or 'None'}

Categories: {", ".join([c.name for c in categories])}
"""
    return context


def process_chat_message(message, user_id=None):
    """
    Process a chat message and generate an AI response.
    The chatbot can answer questions about products, offers, stock, and generate promotions.
    """
    from ai.offer_generator import get_gemini_model
    
    model = get_gemini_model()
    
    if model is None:
        return _fallback_chat_response(message)
    
    # Get store context
    store_context = get_store_context()
    
    prompt = f"""You are RetailMind AI, an intelligent retail store assistant. You help store managers with:
- Answering questions about products, offers, and stock
- Generating promotional announcements
- Providing business insights and recommendations
- Helping with inventory management

Current Store Data:
{store_context}

User Question: "{message}"

Instructions:
- Be helpful, professional, and concise
- Use the store data above to answer accurately
- If asked to generate a promotion, create an engaging announcement
- If asked about low stock, list the products
- If asked about active offers, list them with details
- Provide actionable business recommendations when relevant
- Format your response clearly with bullet points when listing items

Your Response:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f'Chatbot error: {str(e)}')
        return _fallback_chat_response(message)


def _fallback_chat_response(message):
    """Fallback response when Gemini is not available."""
    msg_lower = message.lower()
    
    if 'offer' in msg_lower and ('active' in msg_lower or 'today' in msg_lower):
        return "To check active offers, please visit the Offers page. You can filter by 'Active' status to see all current promotions."
    
    elif 'stock' in msg_lower or 'low stock' in msg_lower:
        return "You can view low stock products on the Products page by filtering with 'Low Stock'. I recommend restocking items below 10 units."
    
    elif 'generate' in msg_lower or 'promotion' in msg_lower or 'announcement' in msg_lower:
        return "I can help you generate a promotion! Please use the AI Generator page where you can type something like 'Rice 20% off till Sunday' and I'll create a professional announcement."
    
    elif 'report' in msg_lower:
        return "You can generate daily, weekly, or monthly reports from the Reports page. Reports include AI-powered summaries and can be exported as PDF or Excel."
    
    elif 'recommend' in msg_lower or 'suggest' in msg_lower:
        return "Based on retail best practices, I recommend:\n- Run promotions on slow-moving products\n- Offer 15-25% discounts on seasonal items\n- Schedule announcements during peak hours (10 AM - 12 PM, 5 PM - 8 PM)\n- Create bundle offers for related products"
    
    else:
        return "I'm RetailMind AI, your intelligent retail assistant! I can help you with:\n- Checking active offers and promotions\n- Monitoring low stock products\n- Generating promotional announcements\n- Creating business reports\n- Providing marketing recommendations\n\nPlease ask me a specific question about your store!"
