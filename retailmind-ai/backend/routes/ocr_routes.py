"""
RetailMind AI - OCR Routes
"""
import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity

from models import db, Offer, Product, User
from utils import admin_required, log_activity, save_upload_file, allowed_file
from ocr.scanner import scan_image, parse_offer_from_ocr_text

ocr_bp = Blueprint('ocr', __name__, url_prefix='/api/ocr')


@ocr_bp.route('/scan', methods=['POST'])
@admin_required
def scan_offer_image():
    """Upload and scan an offer image using OCR."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if not file or not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use PNG, JPG, JPEG, GIF, WebP, or BMP.'}), 400

    # Save uploaded file
    image_url = save_upload_file(file, 'ocr')
    if not image_url:
        return jsonify({'error': 'Failed to save image'}), 500

    # Get full path for OCR
    image_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        image_url.replace('/uploads/', '')
    )

    # Run OCR
    ocr_result = scan_image(image_path)

    if ocr_result.get('error'):
        return jsonify({
            'error': ocr_result['error'],
            'extracted_text': '',
            'offer_data': None,
            'image_url': image_url
        }), 200

    extracted_text = ocr_result.get('text', '')

    if not extracted_text.strip():
        return jsonify({
            'extracted_text': '',
            'offer_data': None,
            'ocr_confidence': 0,
            'image_url': image_url,
            'message': 'No text detected in the image. Try a clearer image with visible text.'
        }), 200

    # Parse extracted text into structured offer data using AI or regex fallback
    offer_data = parse_offer_from_ocr_text(extracted_text)

    log_activity('OCR_SCAN', f'OCR scanned image, extracted: "{extracted_text[:100]}"')

    return jsonify({
        'extracted_text': extracted_text,
        'ocr_confidence': ocr_result.get('confidence', 0),
        'offer_data': offer_data,
        'image_url': image_url,
        'message': 'Image scanned successfully. Review extracted data before saving.'
    }), 200
