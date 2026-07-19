"""
RetailMind AI - Audio Mixer Service
Mixes voice announcements with background music using numpy + ffmpeg.
"""
import os
import logging
import subprocess
import numpy as np
import wave
from datetime import datetime

logger = logging.getLogger(__name__)

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'music')
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audio')
TARGET_SR = 44100


def _get_ffmpeg():
    """Get ffmpeg binary path."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def _load_audio(filepath):
    """Load audio file as numpy float64 array (mono). Supports MP3 and WAV."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.wav':
        return _load_wav(filepath)
    elif ext == '.mp3':
        # Convert MP3 to WAV via ffmpeg, then load
        ffmpeg = _get_ffmpeg()
        if not ffmpeg:
            raise RuntimeError('ffmpeg not available for MP3 decoding')
        tmp_wav = filepath + '.tmp.wav'
        subprocess.run([ffmpeg, '-y', '-i', filepath, '-ar', str(TARGET_SR),
                        '-ac', '1', '-f', 'wav', tmp_wav],
                       capture_output=True, timeout=30)
        if not os.path.exists(tmp_wav):
            raise RuntimeError(f'Failed to decode: {filepath}')
        samples = _load_wav(tmp_wav)
        os.remove(tmp_wav)
        return samples
    else:
        raise ValueError(f'Unsupported format: {ext}')


def _load_wav(filepath):
    """Load WAV file as float64 numpy array."""
    with wave.open(filepath, 'rb') as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth == 2:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32767.0
    elif sampwidth == 4:
        samples = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483647.0
    else:
        samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0

    # Convert stereo to mono
    if n_channels == 2:
        samples = (samples[0::2] + samples[1::2]) / 2.0

    # Resample if needed
    if sr != TARGET_SR:
        ratio = TARGET_SR / sr
        new_len = int(len(samples) * ratio)
        indices = np.linspace(0, len(samples) - 1, new_len)
        samples = np.interp(indices, np.arange(len(samples)), samples)

    return samples


def _save_mp3(samples, filepath, sr=TARGET_SR):
    """Save numpy samples as MP3 (via WAV + ffmpeg)."""
    wav_path = filepath + '.tmp.wav'

    # Normalize and convert to int16
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak * 0.9
    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(wav_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int_samples.tobytes())

    ffmpeg = _get_ffmpeg()
    if ffmpeg:
        subprocess.run([ffmpeg, '-y', '-i', wav_path, '-b:a', '128k', filepath],
                       capture_output=True, timeout=30)
        os.remove(wav_path)
        if os.path.exists(filepath):
            return filepath

    # Fallback: return WAV
    if os.path.exists(wav_path):
        os.rename(wav_path, filepath.replace('.mp3', '.wav'))
        return filepath.replace('.mp3', '.wav')
    return None


def get_available_tracks():
    """List all available background music tracks."""
    tracks = []
    if not os.path.isdir(MUSIC_DIR):
        return tracks

    track_info = {
        'soft-store-ambience': {'name': 'Soft Store Ambience', 'description': 'Warm ambient pad'},
        'light-instrumental': {'name': 'Light Instrumental', 'description': 'Delicate arpeggiated melody'},
        'calm-piano': {'name': 'Calm Piano', 'description': 'Peaceful pentatonic melody'},
        'happy-retail': {'name': 'Happy Retail Music', 'description': 'Upbeat cheerful pattern'},
    }

    for filename in sorted(os.listdir(MUSIC_DIR)):
        if not (filename.endswith('.mp3') or filename.endswith('.wav')):
            continue
        track_id = os.path.splitext(filename)[0]
        info = track_info.get(track_id, {'name': track_id, 'description': ''})
        tracks.append({
            'id': track_id,
            'name': info['name'],
            'description': info['description'],
            'file': filename,
        })
    return tracks


def _find_music_file(track_id):
    """Find music file (mp3 or wav) for a track."""
    for ext in ['.mp3', '.wav']:
        path = os.path.join(MUSIC_DIR, f'{track_id}{ext}')
        if os.path.exists(path):
            return path
    return None


def mix_voice_with_music(voice_path, music_track_id, music_volume_pct=15, output_dir=None):
    """
    Mix a voice recording with background music.

    Args:
        voice_path: Path to voice audio (MP3 or WAV)
        music_track_id: Track ID (e.g. 'calm-piano'), or empty/None for voice-only
        music_volume_pct: Music volume 0-30%. Voice always dominant.
        output_dir: Where to save the mixed file

    Returns:
        Path to mixed audio file, or None on error.
    """
    if not voice_path or not os.path.exists(voice_path):
        logger.error(f'Voice file not found: {voice_path}')
        return None

    music_volume_pct = max(0, min(30, music_volume_pct))

    try:
        voice = _load_audio(voice_path)

        # Voice-only mode
        if not music_track_id or music_volume_pct == 0:
            voice = _apply_fade(voice, 0.2, 1.0)
            return _save_mixed(voice, output_dir, 'voice_only')

        # Find and load music
        music_path = _find_music_file(music_track_id)
        if not music_path:
            logger.warning(f'Music track not found: {music_track_id}, using voice only')
            return _save_mixed(voice, output_dir, 'voice_only')

        music = _load_audio(music_path)

        # Loop music to match voice length
        if len(music) < len(voice):
            repeats = (len(voice) // len(music)) + 1
            music = np.tile(music, repeats)
        music = music[:len(voice) + int(TARGET_SR * 1.0)]  # +1 sec padding
        music = music[:len(voice)]

        # Adjust music volume
        # Map 0-30% to amplitude: 30% = 0.3, 15% = 0.15
        music_gain = music_volume_pct / 100.0
        music = music * music_gain

        # Fade music in (1.5s) and out (2s)
        music = _apply_fade(music, 1.5, 2.0)

        # Mix: voice at full volume + music at reduced volume
        min_len = min(len(voice), len(music))
        mixed = voice[:min_len] + music[:min_len]

        # Subtle overall fade
        mixed = _apply_fade(mixed, 0.2, 1.0)

        return _save_mixed(mixed, output_dir, f'mixed_{music_track_id}')

    except Exception as e:
        logger.error(f'Audio mixing error: {str(e)}')
        return None


def _apply_fade(samples, fade_in_sec=0.0, fade_out_sec=0.0):
    """Apply fade in/out to audio samples."""
    n = len(samples)
    result = samples.copy()

    if fade_in_sec > 0:
        att = min(int(fade_in_sec * TARGET_SR), n // 4)
        if att > 0:
            result[:att] *= np.linspace(0, 1, att)

    if fade_out_sec > 0:
        rel = min(int(fade_out_sec * TARGET_SR), n // 4)
        if rel > 0:
            result[-rel:] *= np.linspace(1, 0, rel)

    return result


def _save_mixed(samples, output_dir, prefix):
    """Save mixed audio and return file path."""
    if not output_dir:
        output_dir = AUDIO_DIR
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{prefix}_{timestamp}.mp3"
    filepath = os.path.join(output_dir, filename)

    return _save_mp3(samples, filepath)
