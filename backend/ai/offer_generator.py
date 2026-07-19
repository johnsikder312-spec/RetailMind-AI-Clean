"""
RetailMind AI - AI Offer Generator using Google Gemini
"""
import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize Gemini client
_gemini_model = None


def get_gemini_model():
    """Get or initialize Gemini model."""
    global _gemini_model
    if _gemini_model is None:
        try:
            import google.generativeai as genai
            api_key = os.getenv('GEMINI_API_KEY', '')
            if api_key and api_key != 'your_gemini_api_key_here':
                genai.configure(api_key=api_key)
                _gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info('Gemini model initialized successfully')
            else:
                logger.warning('Gemini API key not configured - using fallback responses')
                return None
        except Exception as e:
            logger.error(f'Failed to initialize Gemini: {str(e)}')
            return None
    return _gemini_model


def generate_offer_from_text(input_text, language='english'):
    """
    Generate a structured offer from natural language input.
    
    Example input: "Rice 20% off till Sunday"
    Returns structured data with product, discount, dates, and announcement.
    """
    model = get_gemini_model()
    
    if model is None:
        return _fallback_offer_generation(input_text, language)
    
    lang_names = {'hindi': 'Hindi', 'bengali': 'Bengali', 'english': 'English'}
    lang_name = lang_names.get(language, 'English')
    
    if language == 'english':
        language_instruction = 'IMPORTANT: Generate ALL text fields (title, description, announcement_text) in English.'
    else:
        language_instruction = (
            f'CRITICAL LANGUAGE REQUIREMENT: ALL text output MUST be written in {lang_name}. '
            f'This includes the "title", "description", and "announcement_text" fields. '
            f'Do NOT write these fields in English. The entire output must be in {lang_name} only.'
        )
    
    prompt = f"""You are a retail promotion expert. Analyze this offer description and extract structured information.

Input: "{input_text}"

{language_instruction}

Respond ONLY with valid JSON (no markdown, no code blocks) in this exact format:
{{
    "product_name": "detected product name",
    "brand": "detected brand or empty string",
    "category": "most likely category",
    "discount_percent": <number>,
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "title": "attractive offer title in {lang_name}",
    "description": "brief offer description in {lang_name}",
    "announcement_text": "engaging store announcement text for speakers in {lang_name}"
}}

Rules:
- If no end date is mentioned, set it to 7 days from today
- If no start date is mentioned, use today's date
- Make the announcement_text engaging, professional, and suitable for in-store speakers
- The announcement should be 2-3 sentences, enthusiastic and informative
- Today's date is: {datetime.now().strftime('%Y-%m-%d')}
- The title, description, and announcement_text MUST be in {lang_name}
"""
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
        text = text.strip()
        
        result = json.loads(text)
        
        # Ensure all required fields
        result.setdefault('product_name', '')
        result.setdefault('brand', '')
        result.setdefault('category', '')
        result.setdefault('discount_percent', 0)
        result.setdefault('start_date', datetime.now().strftime('%Y-%m-%d'))
        result.setdefault('end_date', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        result.setdefault('title', f"{result.get('product_name', 'Product')} - {result.get('discount_percent', 0)}% Off")
        result.setdefault('description', '')
        result.setdefault('announcement_text', '')
        result['language'] = language
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Gemini response: {str(e)}')
        return _fallback_offer_generation(input_text, language)
    except Exception as e:
        logger.error(f'Gemini API error: {str(e)}')
        return _fallback_offer_generation(input_text, language)


def _fallback_offer_generation(input_text, language='english'):
    """Fallback offer generation when Gemini is not available."""
    import re
    
    # Try to extract discount percentage
    discount_match = re.search(r'(\d+)\s*%', input_text)
    discount = int(discount_match.group(1)) if discount_match else 10
    
    # Try to extract product name (first capitalized word or first word)
    words = input_text.split()
    product_name = words[0] if words else 'Product'
    
    # Try to detect category
    categories = {
        'rice': 'Rice & Grains', 'wheat': 'Rice & Grains', 'grain': 'Rice & Grains',
        'oil': 'Cooking Oil', 'ghee': 'Cooking Oil',
        'tea': 'Beverages', 'coffee': 'Beverages', 'juice': 'Beverages',
        'milk': 'Dairy', 'butter': 'Dairy', 'cheese': 'Dairy',
        'soap': 'Personal Care', 'shampoo': 'Personal Care',
        'chips': 'Snacks', 'biscuit': 'Snacks',
        'apple': 'Fruits & Vegetables', 'banana': 'Fruits & Vegetables',
    }
    
    category = 'General'
    for key, cat in categories.items():
        if key in input_text.lower():
            category = cat
            break
    
    # Generate announcement based on language
    if language == 'hindi':
        announcement = f"ध्यान दें! {product_name} पर {discount}% की विशेष छूट उपलब्ध है। यह ऑफर सीमित समय के लिए है। जल्दी आएं और लाभ उठाएं!"
        title = f'{product_name} - {discount}% विशेष छूट'
        description = f'{product_name} पर विशेष {discount}% छूट'
    elif language == 'bengali':
        announcement = f"মনোযোগ দিন! {product_name}-এ {discount}% বিশেষ ছাড় পাওয়া যাচ্ছে। এই অফার সীমিত সময়ের জন্য। তাড়াতাড়ি আসুন এবং সুবিধা নিন!"
        title = f'{product_name} - {discount}% বিশেষ ছাড়'
        description = f'{product_name}-এ বিশেষ {discount}% ছাড়'
    else:
        announcement = f"Attention shoppers! Don't miss this incredible offer. {product_name} is now available at an exciting {discount}% discount. Visit our store today and save big before this limited-time offer ends!"
        title = f'{product_name} - {discount}% Off Special'
        description = f'Special {discount}% discount on {product_name}'
    
    end_date = datetime.now() + timedelta(days=7)
    
    return {
        'product_name': product_name,
        'brand': '',
        'category': category,
        'discount_percent': discount,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'title': title,
        'description': description,
        'announcement_text': announcement,
        'language': language
    }


def generate_multilingual_announcement(offer_data, target_language):
    """Generate announcement in a different language for an existing offer."""
    model = get_gemini_model()
    
    if model is None:
        return _fallback_multilingual(offer_data, target_language)
    
    lang_map = {'hindi': 'Hindi', 'bengali': 'Bengali', 'english': 'English'}
    lang_name = lang_map.get(target_language, 'English')
    
    prompt = f"""Translate and adapt this store announcement into {lang_name}. Make it natural and engaging for native speakers.

Product: {offer_data.get('product_name', 'Product')}
Discount: {offer_data.get('discount_percent', 10)}%
Original announcement: {offer_data.get('announcement_text', '')}

Respond ONLY with the translated announcement text (no JSON, no formatting):"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f'Translation error: {str(e)}')
        return _fallback_multilingual(offer_data, target_language)


def _fallback_multilingual(offer_data, target_language):
    """Fallback multilingual translation."""
    product = offer_data.get('product_name', 'Product')
    discount = offer_data.get('discount_percent', 10)
    
    if target_language == 'hindi':
        return f"ध्यान दें! {product} पर {discount}% की विशेष छूट। सीमित समय का ऑफर!"
    elif target_language == 'bengali':
        return f"মনোযোগ দিন! {product}-এ {discount}% ছাড়। সীমিত সময়ের অফার!"
    else:
        return f"Attention! {product} at {discount}% off. Limited time offer!"
