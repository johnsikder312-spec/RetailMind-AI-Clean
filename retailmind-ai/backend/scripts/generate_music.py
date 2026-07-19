"""
RetailMind AI - Background Music Track Generator
Generates royalty-free synthesized background music tracks using numpy + wave.
"""
import os
import sys
import numpy as np
import wave
import struct
import subprocess

SAMPLE_RATE = 44100
DURATION_SEC = 30
MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'music')


def _get_ffmpeg():
    """Get ffmpeg binary path from imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def _wav_to_mp3(wav_path, mp3_path):
    """Convert WAV to MP3 using ffmpeg."""
    ffmpeg = _get_ffmpeg()
    if not ffmpeg:
        # Just copy wav as the output
        return wav_path
    subprocess.run([ffmpeg, '-y', '-i', wav_path, '-b:a', '128k', mp3_path],
                   capture_output=True, timeout=30)
    if os.path.exists(mp3_path):
        os.remove(wav_path)  # Clean up WAV
        return mp3_path
    return wav_path


def _save_audio(samples, filename):
    """Save numpy audio samples as MP3 (via WAV + ffmpeg)."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    wav_path = os.path.join(MUSIC_DIR, filename.replace('.mp3', '.wav'))
    mp3_path = os.path.join(MUSIC_DIR, filename)

    # Normalize to 16-bit range
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak * 0.8  # leave headroom
    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(wav_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_samples.tobytes())

    return _wav_to_mp3(wav_path, mp3_path)


def _sine(freq, duration, sr=SAMPLE_RATE):
    """Generate sine wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _triangle(freq, duration, sr=SAMPLE_RATE):
    """Generate triangle wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1


def _envelope(samples, attack_sec=0.5, release_sec=1.0, sr=SAMPLE_RATE):
    """Apply fade in/out envelope."""
    n = len(samples)
    env = np.ones(n)
    att = int(attack_sec * sr)
    rel = int(release_sec * sr)
    if att > 0 and att < n:
        env[:att] = np.linspace(0, 1, att)
    if rel > 0 and rel < n:
        env[-rel:] = np.linspace(1, 0, rel)
    return samples * env


def _note_envelope(samples, attack_sec=0.05, release_sec=0.3, sr=SAMPLE_RATE):
    """Short note envelope."""
    n = len(samples)
    env = np.ones(n)
    att = int(attack_sec * sr)
    rel = int(release_sec * sr)
    if att > 0 and att < n:
        env[:att] = np.linspace(0, 1, att)
    if rel > 0 and rel < n:
        env[-rel:] = np.linspace(1, 0, rel)
    return samples * env


def generate_soft_store_ambience():
    """Warm ambient pad - slow chord progressions."""
    chords = [
        [261.63, 329.63, 392.00, 493.88],  # Cmaj7
        [220.00, 261.63, 329.63, 392.00],   # Am7
        [174.61, 220.00, 261.63, 329.63],   # Fmaj7
        [196.00, 246.94, 293.66, 349.23],   # G7
    ]
    chord_dur = DURATION_SEC / len(chords)
    track = np.array([], dtype=np.float64)

    for freqs in chords:
        pad = np.zeros(int(SAMPLE_RATE * chord_dur))
        for freq in freqs:
            pad += _sine(freq, chord_dur) * 0.2
            pad += _sine(freq * 2, chord_dur) * 0.05  # subtle harmonic
        pad = _envelope(pad, attack_sec=chord_dur * 0.3, release_sec=chord_dur * 0.3)
        track = np.concatenate([track, pad])

    track = _envelope(track, attack_sec=2.0, release_sec=3.0)
    return track


def generate_light_instrumental():
    """Light melodic pattern with soft pad background."""
    scale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    pattern = [0, 2, 4, 5, 4, 2, 0, 2, 4, 7, 5, 4, 2, 0, 4, 2]

    # Background pad (soft C chord)
    pad = np.zeros(int(SAMPLE_RATE * DURATION_SEC))
    for freq in [130.81, 164.81, 196.00]:
        pad += _sine(freq, DURATION_SEC) * 0.08
    pad = _envelope(pad, 2.0, 2.0)

    # Arpeggiated melody
    note_dur = DURATION_SEC / len(pattern)
    melody = np.array([], dtype=np.float64)
    for idx in pattern:
        freq = scale[idx % len(scale)]
        tone = _triangle(freq, note_dur) * 0.3 + _sine(freq, note_dur) * 0.2
        tone = _note_envelope(tone, 0.03, note_dur * 0.4)
        melody = np.concatenate([melody, tone])

    # Ensure same length
    min_len = min(len(pad), len(melody))
    track = pad[:min_len] + melody[:min_len]
    track = _envelope(track, 1.0, 2.0)
    return track


def generate_calm_piano():
    """Peaceful pentatonic melody with gentle tones."""
    notes = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]
    melody = [0, 2, 4, 2, 3, 1, 0, 4, 5, 3, 2, 0, 1, 3, 2, 4]

    note_dur = DURATION_SEC / len(melody)
    track = np.array([], dtype=np.float64)

    for idx in melody:
        freq = notes[idx]
        # Piano-like: fundamental + soft octave below
        tone = _sine(freq, note_dur) * 0.35 + _sine(freq * 0.5, note_dur) * 0.12
        # Add subtle second harmonic for warmth
        tone += _sine(freq * 2, note_dur) * 0.04
        tone = _note_envelope(tone, 0.02, note_dur * 0.5)
        track = np.concatenate([track, tone])

    # Simple reverb: overlay delayed copy
    delay_samples = int(0.2 * SAMPLE_RATE)
    reverb = np.zeros(len(track) + delay_samples)
    reverb[:len(track)] += track
    reverb[delay_samples:delay_samples + len(track)] += track * 0.3
    track = reverb[:len(track)]

    track = _envelope(track, 1.5, 3.0)
    return track


def generate_happy_retail():
    """Upbeat cheerful pattern with bass and melody."""
    c_notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    pattern = [0, 4, 2, 5, 0, 4, 7, 5, 4, 2, 0, 4, 2, 5, 4, 0]

    note_dur = DURATION_SEC / len(pattern)
    short_note = note_dur * 0.65

    # Melody (staccato triangle)
    melody = np.array([], dtype=np.float64)
    for idx in pattern:
        freq = c_notes[idx]
        tone = _triangle(freq, short_note) * 0.25 + _sine(freq, short_note) * 0.15
        tone = _note_envelope(tone, 0.01, short_note * 0.3)
        silence = np.zeros(int(SAMPLE_RATE * (note_dur - short_note)))
        melody = np.concatenate([melody, tone, silence])

    # Bass line
    bass_pattern = [0, 0, 3, 3, 4, 4, 0, 0]
    bass_note_dur = DURATION_SEC / len(bass_pattern)
    bass = np.array([], dtype=np.float64)
    for idx in bass_pattern:
        freq = c_notes[idx] * 0.5
        tone = _sine(freq, bass_note_dur) * 0.2
        tone = _note_envelope(tone, 0.01, bass_note_dur * 0.3)
        bass = np.concatenate([bass, tone])

    # Combine
    min_len = min(len(melody), len(bass))
    track = melody[:min_len] + bass[:min_len]
    track = _envelope(track, 1.0, 2.0)
    return track


TRACKS = {
    'soft-store-ambience': {'name': 'Soft Store Ambience', 'gen': generate_soft_store_ambience},
    'light-instrumental': {'name': 'Light Instrumental', 'gen': generate_light_instrumental},
    'calm-piano': {'name': 'Calm Piano', 'gen': generate_calm_piano},
    'happy-retail': {'name': 'Happy Retail Music', 'gen': generate_happy_retail},
}


def generate_all_tracks():
    """Generate all background music tracks."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    for track_id, info in TRACKS.items():
        mp3_path = os.path.join(MUSIC_DIR, f'{track_id}.mp3')
        wav_path = os.path.join(MUSIC_DIR, f'{track_id}.wav')
        if os.path.exists(mp3_path) or os.path.exists(wav_path):
            print(f'  [SKIP] {info["name"]} already exists')
            continue
        print(f'  [GEN] {info["name"]}...')
        samples = info['gen']()
        result = _save_audio(samples, f'{track_id}.mp3')
        size_kb = os.path.getsize(result) / 1024
        ext = os.path.splitext(result)[1]
        print(f'  [OK] {os.path.basename(result)} ({size_kb:.0f} KB, {ext})')
    print(f'\nDone! Tracks in: {MUSIC_DIR}')


if __name__ == '__main__':
    print('RetailMind AI - Background Music Generator')
    print('=' * 50)
    generate_all_tracks()
