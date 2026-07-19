"""
RetailMind AI - Text-to-Speech Engine using gTTS
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_speech(text, language='en', output_dir=None):
    """
    Generate speech audio from text using gTTS.
    Returns the path to the generated audio file.
    """
    if not text:
        return None
    
    try:
        from gtts import gTTS
        
        # Language mapping
        lang_map = {
            'en': 'en',
            'english': 'en',
            'hi': 'hi',
            'hindi': 'hi',
            'bn': 'bn',
            'bengali': 'bn'
        }
        
        lang_code = lang_map.get(language.lower(), 'en')
        
        # Create output directory
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audio')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"announcement_{timestamp}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Generate speech
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filepath)
        
        logger.info(f'Speech generated: {filepath}')
        return filepath
        
    except ImportError:
        logger.error('gTTS not installed. Run: pip install gTTS')
        return None
    except Exception as e:
        logger.error(f'TTS generation error: {str(e)}')
        return None


def get_audio_url(filepath):
    """Convert file path to URL path for serving."""
    if not filepath:
        return None
    # Convert absolute path to relative URL
    audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audio')
    if filepath.startswith(audio_dir):
        filename = os.path.basename(filepath)
        return f"/audio/{filename}"
    return None
