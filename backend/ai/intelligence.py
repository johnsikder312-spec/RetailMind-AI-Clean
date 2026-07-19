"""
RetailMind AI - Business Intelligence using Google Gemini
"""
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache for recommendations
_recommendations_cache = {
    'data': None,
    'timestamp': None
}


def get_business_recommendations(force_refresh=False):
    """
    Analyze store data and generate AI-powered business recommendations.
    Results are cached for 1 hour.
    """
    global _recommendations_cache
    
    # Check cache
    if not force_refresh and _recommendations_cache['data']:
        if _recommendations_cache['timestamp']:
            elapsed = (datetime.utcnow() - _recommendations_cache['timestamp']).total_seconds()
            if elapsed < 3600:  # 1 hour cache
                return _recommendations_cache['data']
    
    from models import db, Product, Offer, Category
    from ai.offer_generator import get_gemini_model
    
    now = datetime.utcnow()
    
    # Gather data
    products = Product.query.all()
    active_offers = Offer.query.filter(
        Offer.is_active == True,
        (Offer.end_date == None) | (Offer.end_date > now)
    ).all()
    
    # Identify slow-moving products (high stock, no active offers)
    slow_moving = [p for p in products if p.stock_quantity > 50]
    
    # Products needing promotion (high stock, no current offer)
    offered_product_ids = [o.product_id for o in active_offers if o.product_id]
    needs_promotion = [p for p in products if p.id not in offered_product_ids and p.stock_quantity > 20]
    
    # Low stock alerts
    low_stock = [p for p in products if p.stock_quantity < 10]
    
    # Seasonal analysis
    month = now.month
    seasonal_suggestions = _get_seasonal_suggestions(month)
    
    model = get_gemini_model()
    
    if model is not None:
        try:
            ai_recommendations = _generate_ai_recommendations(
                model, products, active_offers, slow_moving, low_stock, month
            )
        except Exception as e:
            logger.error(f'AI recommendations error: {str(e)}')
            ai_recommendations = _fallback_recommendations(slow_moving, needs_promotion, low_stock)
    else:
        ai_recommendations = _fallback_recommendations(slow_moving, needs_promotion, low_stock)
    
    result = {
        'slow_moving_products': [p.to_dict() for p in slow_moving[:5]],
        'needs_promotion': [p.to_dict() for p in needs_promotion[:5]],
        'low_stock_alerts': [p.to_dict() for p in low_stock[:5]],
        'seasonal_suggestions': seasonal_suggestions,
        'ai_recommendations': ai_recommendations,
        'generated_at': now.isoformat()
    }
    
    # Update cache
    _recommendations_cache['data'] = result
    _recommendations_cache['timestamp'] = now
    
    return result


def _generate_ai_recommendations(model, products, offers, slow_moving, low_stock, month):
    """Generate AI-powered recommendations using Gemini."""
    product_data = '\n'.join([
        f"- {p.name}: stock={p.stock_quantity}, price=₹{p.price}, discount={p.discount}%"
        for p in products[:20]
    ])
    
    offer_data = '\n'.join([
        f"- {o.title}: {o.discount_percent}% off"
        for o in offers[:10]
    ]) or 'No active offers'
    
    prompt = f"""You are a retail business analyst. Analyze this store data and provide actionable recommendations.

Current Month: {['January','February','March','April','May','June','July','August','September','October','November','December'][month-1]}

Products (sample):
{product_data or 'No products'}

Active Offers:
{offer_data}

Slow-moving products (>50 units): {len(slow_moving)}
Low stock products (<10 units): {len(low_stock)}

Provide recommendations in this JSON format (respond ONLY with valid JSON, no markdown):
{{
    "discount_suggestions": [
        {{"product": "name", "suggested_discount": "percentage", "reason": "why"}}
    ],
    "best_timing": "best time for announcements",
    "marketing_tips": ["tip1", "tip2", "tip3"],
    "inventory_alerts": ["alert1", "alert2"]
}}

Limit to 3-5 items per array. Be specific and actionable."""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    if text.startswith('```'):
        text = text.split('\n', 1)[1]
    if text.endswith('```'):
        text = text.rsplit('```', 1)[0]
    
    return json.loads(text.strip())


def _fallback_recommendations(slow_moving, needs_promotion, low_stock):
    """Fallback recommendations without AI."""
    discount_suggestions = []
    for p in slow_moving[:3]:
        discount_suggestions.append({
            'product': p.name,
            'suggested_discount': '20-30%',
            'reason': f'High stock ({p.stock_quantity} units) - needs promotion to move inventory'
        })
    
    return {
        'discount_suggestions': discount_suggestions,
        'best_timing': 'Schedule announcements during peak hours: 10 AM - 12 PM and 5 PM - 8 PM',
        'marketing_tips': [
            'Create bundle offers for related products',
            'Run weekend flash sales on perishable items',
            'Use seasonal themes for promotional campaigns'
        ],
        'inventory_alerts': [
            f'{len(low_stock)} products need restocking',
            f'{len(slow_moving)} products have excess inventory'
        ] if low_stock or slow_moving else ['Inventory levels are balanced']
    }


def _get_seasonal_suggestions(month):
    """Get seasonal promotion suggestions based on current month."""
    seasonal = {
        1: ['New Year Sale', 'Winter Clearance', 'Republic Day Special (Jan 26)'],
        2: ["Valentine's Day Offers", 'Winter End Sale', 'School Reopening Deals'],
        3: ['Holi Festival Sale', 'Spring Collection', 'Financial Year End Offers'],
        4: ['Summer Kick-off Sale', 'Ramzan Special Offers', 'School Summer Vacation Deals'],
        5: ['Summer Sale - Cool Drinks & Ice Creams', 'Mother\'s Day Special'],
        6: ['Summer Peak Sale', 'Eid Special Offers', 'Mango Festival'],
        7: ['Monsoon Sale', 'Rainy Season Essentials'],
        8: ['Independence Day Sale (Aug 15)', 'Raksha Bandhan Special', 'Back to School'],
        9: ['Ganesh Chaturthi Offers', 'Autumn Collection Launch'],
        10: ['Dussehra Sale', 'Navratri Special', 'Pre-Diwali Offers'],
        11: ['Diwali Mega Sale', 'Dhanteras Special', 'Winter Collection Launch'],
        12: ['Christmas Sale', 'Year End Clearance', 'New Year Eve Special', 'Winter Festival']
    }
    
    return seasonal.get(month, ['Seasonal promotions available'])
