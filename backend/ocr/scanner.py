"""
RetailMind AI - OCR Scanner using EasyOCR
"""
import os
import sys
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

_ocr_reader = None
_init_attempted = False


def init_ocr_reader():
    """
    Initialize EasyOCR reader eagerly (call on app startup).
    Sets UTF-8 encoding to avoid Windows cp1252 issues with progress bars.
    """
    global _ocr_reader, _init_attempted
    if _init_attempted:
        return _ocr_reader
    _init_attempted = True

    # Fix Windows console encoding for EasyOCR download progress
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    try:
        import easyocr
        logger.info('Initializing EasyOCR reader (downloading models if needed)...')
        _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        logger.info('EasyOCR reader initialized successfully')
    except ImportError:
        logger.error('easyocr not installed. Run: pip install easyocr')
    except Exception as e:
        logger.error(f'Failed to initialize EasyOCR: {str(e)}')

    return _ocr_reader


def get_ocr_reader():
    """Get the initialized EasyOCR reader, or initialize if not yet done."""
    global _ocr_reader
    if _ocr_reader is None and not _init_attempted:
        return init_ocr_reader()
    return _ocr_reader


def scan_image(image_path):
    """
    Scan an image file and extract text using OCR.
    Returns extracted text and confidence scores.
    """
    reader = get_ocr_reader()

    if reader is None:
        return {
            'error': 'OCR engine not available. EasyOCR may not be installed. Run: pip install easyocr',
            'text': '',
            'results': []
        }

    if not os.path.exists(image_path):
        return {'error': f'Image file not found: {image_path}', 'text': '', 'results': []}

    try:
        logger.info(f'Running OCR on: {image_path}')
        results = reader.readtext(image_path)

        extracted_text = ' '.join([text for _, text, _ in results])
        detailed_results = [
            {
                'text': text,
                'confidence': round(float(conf), 2),
                'bbox': [[int(p[0]), int(p[1])] for p in bbox]
            }
            for bbox, text, conf in results
        ]

        avg_confidence = round(
            sum(float(conf) for _, _, conf in results) / len(results) if results else 0, 2
        )

        logger.info(f'OCR complete: {len(results)} text regions found, avg confidence: {avg_confidence}')

        return {
            'text': extracted_text,
            'results': detailed_results,
            'confidence': avg_confidence
        }
    except Exception as e:
        logger.error(f'OCR scan error: {str(e)}')
        return {'error': f'OCR scan failed: {str(e)}', 'text': '', 'results': []}


def parse_offer_from_ocr_text(text):
    """
    Parse OCR extracted text to identify products, discounts, and offers.
    Uses Gemini AI if available, otherwise uses regex fallback.
    """
    from ai.offer_generator import get_gemini_model

    model = get_gemini_model()

    if model is not None:
        return _ai_parse_ocr_text(model, text)
    else:
        return _fallback_parse_ocr_text(text)


def _ai_parse_ocr_text(model, text):
    """Use Gemini to parse OCR text into structured offer data."""
    prompt = f"""Analyze this text extracted from a promotional poster/flyer and extract offer details.

Extracted Text: "{text}"

Respond ONLY with valid JSON (no markdown):
{{
    "product_name": "detected product or empty",
    "brand": "detected brand or empty",
    "category": "most likely category",
    "discount_percent": <number or 0>,
    "original_price": <number or null>,
    "offer_price": <number or null>,
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "title": "generated offer title",
    "description": "offer description",
    "announcement_text": "in-store announcement text",
    "confidence": "high/medium/low"
}}

If the text doesn't contain clear offer information, still try to extract whatever is relevant.
Today's date is: {datetime.now().strftime('%Y-%m-%d')}"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1]
        if result_text.endswith('```'):
            result_text = result_text.rsplit('```', 1)[0]

        return json.loads(result_text.strip())
    except Exception as e:
        logger.error(f'AI OCR parsing error: {str(e)}')
        return _fallback_parse_ocr_text(text)


def _fallback_parse_ocr_text(text):
    """Fallback OCR text parsing using regex."""
    result = {
        'product_name': '',
        'brand': '',
        'category': 'General',
        'discount_percent': 0,
        'original_price': None,
        'offer_price': None,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': None,
        'title': '',
        'description': '',
        'announcement_text': '',
        'confidence': 'low'
    }

    text_lower = text.lower()

    # Extract discount percentage
    discount_match = re.search(r'(\d+)\s*%\s*(off|discount|छूट|छुट)', text, re.IGNORECASE)
    if discount_match:
        result['discount_percent'] = int(discount_match.group(1))
    else:
        # Try standalone percentage
        pct_match = re.search(r'(\d+)\s*%', text)
        if pct_match:
            result['discount_percent'] = int(pct_match.group(1))

    # Extract prices (₹, Rs., or just numbers that look like prices)
    price_matches = re.findall(r'[₹]\s*(\d+[\d,.]*)', text)
    if not price_matches:
        price_matches = re.findall(r'(?:Rs\.?|INR)\s*(\d+[\d,.]*)', text, re.IGNORECASE)
    if not price_matches:
        # Generic number extraction for prices
        price_matches = re.findall(r'(?<!\d)(\d{2,4}(?:\.\d{2})?)(?!\d)', text)

    clean_prices = [float(p.replace(',', '')) for p in price_matches if p.replace(',', '').replace('.', '').isdigit()]
    if len(clean_prices) >= 2:
        result['original_price'] = clean_prices[0]
        result['offer_price'] = clean_prices[1]
    elif len(clean_prices) == 1:
        result['offer_price'] = clean_prices[0]

    # Try to detect product name
    product_keywords = {
        'rice': 'Rice', 'basmati': 'Basmati Rice', 'wheat': 'Wheat', 'atta': 'Wheat Flour',
        'oil': 'Cooking Oil', 'ghee': 'Ghee', 'sugar': 'Sugar', 'salt': 'Salt',
        'tea': 'Tea', 'coffee': 'Coffee', 'milk': 'Milk', 'butter': 'Butter',
        'soap': 'Soap', 'shampoo': 'Shampoo', 'chips': 'Chips', 'biscuit': 'Biscuits',
        'dal': 'Dal', 'lentil': 'Lentils', 'onion': 'Onion', 'potato': 'Potato',
        'tomato': 'Tomato', 'apple': 'Apple', 'banana': 'Banana', 'mango': 'Mango',
    }

    detected_product = ''
    for key, name in product_keywords.items():
        if key in text_lower:
            detected_product = name
            break

    # If no keyword match, use first significant word
    if not detected_product:
        words = [w for w in text.split() if len(w) > 2 and not w.isdigit() and w.lower() not in ('off', 'sale', 'discount', 'special', 'offer', 'price', 'only', 'now')]
        if words:
            detected_product = words[0].title()

    result['product_name'] = detected_product

    # Try to detect brand
    brand_words = [w for w in text.split() if w[0:1].isupper() and len(w) > 2 and w.lower() not in ('sale', 'Off', 'Special', 'Offer', 'Price', 'Only', 'Now', 'Buy', 'Get', 'Free')]
    if brand_words and brand_words[0] != detected_product:
        result['brand'] = brand_words[0]

    # Detect category
    categories = {
        'rice': 'Rice & Grains', 'wheat': 'Rice & Grains', 'grain': 'Rice & Grains', 'dal': 'Rice & Grains', 'atta': 'Rice & Grains',
        'oil': 'Cooking Oil', 'ghee': 'Cooking Oil',
        'tea': 'Beverages', 'coffee': 'Beverages', 'juice': 'Beverages',
        'milk': 'Dairy', 'butter': 'Dairy', 'cheese': 'Dairy',
        'soap': 'Personal Care', 'shampoo': 'Personal Care',
        'chips': 'Snacks', 'biscuit': 'Snacks',
        'apple': 'Fruits & Vegetables', 'banana': 'Fruits & Vegetables', 'onion': 'Fruits & Vegetables',
        'tomato': 'Fruits & Vegetables', 'potato': 'Fruits & Vegetables', 'mango': 'Fruits & Vegetables',
    }
    for key, cat in categories.items():
        if key in text_lower:
            result['category'] = cat
            break

    # Generate title and announcement
    if result['product_name'] and result['discount_percent']:
        result['title'] = f"{result['product_name']} - {result['discount_percent']}% Off"
        result['description'] = f"Special {result['discount_percent']}% discount on {result['product_name']}"
        result['announcement_text'] = (
            f"Attention shoppers! {result['product_name']} is now available at "
            f"{result['discount_percent']}% discount. Don't miss this amazing offer!"
        )
        result['confidence'] = 'medium'
    elif result['product_name']:
        result['title'] = f"{result['product_name']} - Special Offer"
        result['description'] = f"Special offer on {result['product_name']}"
        result['announcement_text'] = f"Check out our special offer on {result['product_name']}!"
        result['confidence'] = 'low'
    elif result['discount_percent']:
        result['title'] = f"{result['discount_percent']}% Off Special"
        result['description'] = f"Get {result['discount_percent']}% off on selected items"
        result['announcement_text'] = f"Don't miss our {result['discount_percent']}% discount on selected items!"
        result['confidence'] = 'low'

    return result
