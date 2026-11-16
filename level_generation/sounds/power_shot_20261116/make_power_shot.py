#!/usr/bin/env python3
"""Builds the Power Shot layer (talent_power_shot.wav): played with the ordinary bow shot (`shoot bow01.wav`), it
makes the shot sound heavier and charged. Made from the bow shot itself plus synthesis, no outside service:

- the bow shot an octave down, low-passed: a deeper body under the normal twang;
- a sub thump (a falling sine) at the release;
- a rising, then cut, band-passed noise whoosh: the charged arrow leaving;
- a short inharmonic metallic shimmer (the shot's golden-green glow);
- soft tanh saturation, then the peak set to the talent sounds' level.

Usage: make_power_shot.py [--out DIR]   writes out/v1.wav, v2.wav, v3.wav (three takes of the same recipe:
v1 balanced, v2 heavier and darker, v3 brighter with more shimmer). Installing a take: copy it to
assets_dev/engine/audio/solo_talents/talent_power_shot.wav (picks.yml records the choice).
"""
import argparse
import os
import subprocess
import tempfile

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BOW = os.path.join(REPO, 'assets_dev', 'engine', 'audio', 'shoot bow01.wav')
RATE = 48000

TAKES = {
    'v1': dict(body=0.6, sub=0.4, whoosh=0.8, shimmer=0.35, drive=1.6, brightness=1.0),
    'v2': dict(body=0.8, sub=0.55, whoosh=0.7, shimmer=0.2, drive=2.0, brightness=0.8),
    'v3': dict(body=0.5, sub=0.35, whoosh=0.85, shimmer=0.55, drive=1.4, brightness=1.25),
}


def load_bow():
    # The game's file is IMA ADPCM at 22050 Hz; ffmpeg decodes it to 48 kHz float.
    with tempfile.TemporaryDirectory() as folder:
        decoded = os.path.join(folder, 'bow.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', BOW, '-ac', '1', '-ar', str(RATE), '-c:a', 'pcm_f32le',
                        decoded], check=True)
        rate, data = wavfile.read(decoded)
    data = data.astype(np.float64)
    return data / max(1e-9, np.max(np.abs(data)))


def envelope(length, attack, decay, rate=RATE):
    t = np.arange(length) / rate
    rise = np.clip(t / max(attack, 1e-4), 0.0, 1.0)
    return rise * np.exp(-np.maximum(0.0, t - attack) / decay)


def octave_down(bow, length):
    # Read the shot at half speed: an octave lower and twice as long.
    positions = np.arange(len(bow) * 2) / 2.0
    slowed = np.interp(positions, np.arange(len(bow)), bow)
    b, a = signal.butter(4, 1800 / (RATE / 2), 'low')
    slowed = signal.lfilter(b, a, slowed)
    out = np.zeros(length)
    out[:min(length, len(slowed))] = slowed[:length]
    return out


def sub_thump(length):
    t = np.arange(length) / RATE
    frequency = 40 + 55 * np.exp(-t / 0.05)
    phase = 2 * np.pi * np.cumsum(frequency) / RATE
    return np.sin(phase) * envelope(length, 0.004, 0.11)


def whoosh(length, rng, brightness):
    noise = rng.standard_normal(length)
    out = np.zeros(length)
    # A band that climbs from about 500 Hz to 3 kHz as the arrow leaves, in short blocks.
    block = 480
    sos_state = None
    for start in range(0, length, block):
        fraction = start / length
        centre = (500 + 2500 * min(1.0, fraction * 2.2)) * brightness
        low, high = centre * 0.6, min(centre * 1.6, RATE / 2 - 100)
        sos = signal.butter(2, [low / (RATE / 2), high / (RATE / 2)], 'band', output='sos')
        if sos_state is None:
            sos_state = signal.sosfilt_zi(sos) * 0.0
        out[start:start + block], sos_state = signal.sosfilt(sos, noise[start:start + block], zi=sos_state)
    t = np.arange(length) / RATE
    # Swells over the first 60 ms (a pre-release charge), then trails off.
    shape = np.clip(t / 0.06, 0, 1) ** 1.5 * np.exp(-np.maximum(0, t - 0.06) / 0.16)
    return out / max(1e-9, np.max(np.abs(out))) * shape


def shimmer(length, rng, brightness):
    t = np.arange(length) / RATE
    out = np.zeros(length)
    # Inharmonic partials, as a struck bell-like ring of force; each with a slight detune beat.
    for frequency, weight, decay in ((1870, 1.0, 0.22), (2730, 0.7, 0.16), (4120, 0.45, 0.11), (5900, 0.3, 0.07)):
        f = frequency * brightness
        beat = 1 + 0.004 * np.sin(2 * np.pi * 7 * t)
        out += weight * np.sin(2 * np.pi * f * beat * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / decay)
    return out * envelope(length, 0.008, 1.0) / 2.45


def build(take, seed):
    rng = np.random.default_rng(seed)
    length = int(0.7 * RATE)
    bow = load_bow()
    mix = (take['body'] * octave_down(bow, length)
           + take['sub'] * sub_thump(length)
           + take['whoosh'] * whoosh(length, rng, take['brightness'])
           + take['shimmer'] * shimmer(length, rng, take['brightness']))
    mix = np.tanh(take['drive'] * mix) / np.tanh(take['drive'])
    # Fade the tail, cut DC and rumble below 30 Hz, peak at -8 dBFS like the other talent sounds.
    fade = int(0.08 * RATE)
    mix[-fade:] *= np.linspace(1, 0, fade)
    b, a = signal.butter(2, 30 / (RATE / 2), 'high')
    mix = signal.lfilter(b, a, mix)
    return mix / np.max(np.abs(mix)) * 10 ** (-8 / 20)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', default=os.path.join(HERE, 'out'))
    args = parser.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for index, (name, take) in enumerate(TAKES.items()):
        path = os.path.join(args.out, name + '.wav')
        wavfile.write(path, RATE, (build(take, 1100 + index) * 32767).astype(np.int16))
        print(path)


if __name__ == '__main__':
    main()
