"""
RetailMind AI - TTS Routes
"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import get_jwt_identity
from datetime import datetime

from models import db, Announcement, Offer
from utils import admin_required, log_activity
from tts.engine import generate_speech, get_audio_url

tts_bp = Blueprint('tts', __name__, url_prefix='/api/tts')


@tts_bp.route('/generate', methods=['POST'])
@admin_required
def generate_tts():
    """Generate speech from text."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'error': 'Text is required'}), 400
    
    text = data['text'].strip()
    language = data.get('language', 'english')
    offer_id = data.get('offer_id')
    
    # Generate speech
    audio_path = generate_speech(text, language)
    
    if not audio_path:
        return jsonify({'error': 'Failed to generate speech'}), 500
    
    audio_url = get_audio_url(audio_path)
    
    # Create announcement record if offer_id provided
    announcement = None
    if offer_id:
        offer = Offer.query.get(offer_id)
        if offer:
            announcement = Announcement(
                offer_id=offer_id,
                audio_file_path=audio_path,
                language=language,
                is_active=True
            )
            db.session.add(announcement)
            db.session.commit()
    
    log_activity('TTS_GENERATED', f'Speech generated for text: "{text[:50]}..."')
    
    return jsonify({
        'audio_url': audio_url,
        'announcement': announcement.to_dict() if announcement else None,
        'message': 'Speech generated successfully'
    }), 200


@tts_bp.route('/announce/<int:announcement_id>', methods=['POST'])
@admin_required
def announce_now(announcement_id):
    """Trigger an immediate announcement playback."""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if not announcement.audio_file_path or not os.path.exists(announcement.audio_file_path):
        return jsonify({'error': 'Audio file not found'}), 404
    
    announcement.last_played = datetime.utcnow()
    db.session.commit()
    
    audio_url = get_audio_url(announcement.audio_file_path)
    
    log_activity('ANNOUNCEMENT_PLAYED', f'Announcement #{announcement_id} played')
    
    return jsonify({
        'audio_url': audio_url,
        'announcement': announcement.to_dict(),
        'message': 'Announcement triggered'
    }), 200


@tts_bp.route('/schedule/<int:announcement_id>', methods=['POST'])
@admin_required
def schedule_announcement(announcement_id):
    """Set up scheduled announcement playback."""
    announcement = Announcement.query.get_or_404(announcement_id)
    data = request.get_json() or {}
    
    interval = data.get('interval', 30)  # Default 30 minutes
    if interval not in [15, 30, 60]:
        return jsonify({'error': 'Interval must be 15, 30, or 60 minutes'}), 400
    
    announcement.scheduled_interval = interval
    announcement.is_active = True
    db.session.commit()
    
    # Register with scheduler
    from services.scheduler import register_announcement_schedule
    register_announcement_schedule(announcement.id, interval)
    
    log_activity('ANNOUNCEMENT_SCHEDULED', f'Announcement #{announcement_id} scheduled every {interval} min')
    
    return jsonify({
        'announcement': announcement.to_dict(),
        'message': f'Announcement scheduled every {interval} minutes'
    }), 200


@tts_bp.route('/stop/<int:announcement_id>', methods=['POST'])
@admin_required
def stop_announcement(announcement_id):
    """Stop scheduled announcement."""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    announcement.is_active = False
    db.session.commit()
    
    # Remove from scheduler
    from services.scheduler import unregister_announcement_schedule
    unregister_announcement_schedule(announcement.id)
    
    log_activity('ANNOUNCEMENT_STOPPED', f'Announcement #{announcement_id} stopped')
    
    return jsonify({
        'announcement': announcement.to_dict(),
        'message': 'Announcement stopped'
    }), 200


@tts_bp.route('/list', methods=['GET'])
@admin_required
def list_announcements():
    """List all announcements."""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify({
        'announcements': [a.to_dict() for a in announcements]
    }), 200


@tts_bp.route('/music-tracks', methods=['GET'])
@admin_required
def list_music_tracks():
    """List available background music tracks."""
    from services.audio_mixer import get_available_tracks
    tracks = get_available_tracks()
    return jsonify({'tracks': tracks}), 200


@tts_bp.route('/preview', methods=['POST'])
@admin_required
def preview_announcement():
    """Generate a preview: TTS voice + background music (no DB save)."""
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({'error': 'Text is required'}), 400

    text = data['text'].strip()
    language = data.get('language', 'english')
    music_track = data.get('background_music', '')
    music_volume = int(data.get('music_volume', 15))

    # Generate TTS voice
    voice_path = generate_speech(text, language)
    if not voice_path:
        return jsonify({'error': 'Failed to generate speech'}), 500

    # Mix with music if selected
    if music_track and music_volume > 0:
        from services.audio_mixer import mix_voice_with_music
        mixed_path = mix_voice_with_music(voice_path, music_track, music_volume)
        if mixed_path:
            audio_url = get_audio_url(mixed_path)
            return jsonify({
                'audio_url': audio_url,
                'message': 'Preview generated with background music'
            }), 200

    # Voice only fallback
    audio_url = get_audio_url(voice_path)
    return jsonify({
        'audio_url': audio_url,
        'message': 'Preview generated (voice only)'
    }), 200


@tts_bp.route('/mix/<int:announcement_id>', methods=['POST'])
@admin_required
def mix_announcement(announcement_id):
    """Re-mix an existing announcement with background music and save."""
    announcement = Announcement.query.get_or_404(announcement_id)
    data = request.get_json() or {}

    music_track = data.get('background_music', '')
    music_volume = int(data.get('music_volume', 15))

    # Get the original voice file from the offer's TTS
    # First, generate fresh TTS from the offer's announcement text
    if not announcement.offer or not announcement.offer.announcement_text:
        return jsonify({'error': 'No announcement text available'}), 400

    offer = announcement.offer
    voice_path = generate_speech(offer.announcement_text, offer.language or 'english')
    if not voice_path:
        return jsonify({'error': 'Failed to generate speech'}), 500

    # Mix
    from services.audio_mixer import mix_voice_with_music
    mixed_path = None
    if music_track and music_volume > 0:
        mixed_path = mix_voice_with_music(voice_path, music_track, music_volume)

    final_path = mixed_path or voice_path

    # Update announcement record
    announcement.audio_file_path = final_path
    announcement.background_music = music_track
    announcement.music_volume = music_volume
    db.session.commit()

    audio_url = get_audio_url(final_path)
    log_activity('ANNOUNCEMENT_MIXED', f'Announcement #{announcement_id} mixed with music: {music_track or "none"}')

    return jsonify({
        'announcement': announcement.to_dict(),
        'audio_url': audio_url,
        'message': 'Announcement mixed and saved'
    }), 200


@tts_bp.route('/download/<int:announcement_id>', methods=['GET'])
@admin_required
def download_announcement(announcement_id):
    """Download announcement audio file."""
    announcement = Announcement.query.get_or_404(announcement_id)

    if not announcement.audio_file_path or not os.path.exists(announcement.audio_file_path):
        return jsonify({'error': 'Audio file not found'}), 404

    return send_file(
        announcement.audio_file_path,
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name=f'announcement_{announcement.id}.mp3'
    )


@tts_bp.route('/music/<filename>', methods=['GET'])
def serve_music(filename):
    """Serve background music files."""
    music_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'music')
    filepath = os.path.join(music_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, mimetype='audio/mpeg')


@tts_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve audio files."""
    audio_dir = current_app.config.get('AUDIO_FOLDER', os.path.join(os.path.dirname(__file__), '..', 'audio'))
    filepath = os.path.join(audio_dir, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, mimetype='audio/mpeg')

