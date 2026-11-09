#!/usr/bin/env python3
"""Synthesise the Blaster Shotgun firing sound from the stock blaster shot.

Seven pitch-spread, slightly staggered copies of `shoot blaster01.wav` form the scatter volley; a low
thump and filtered noise crack give it shotgun weight; a falling whine and a two-click recharge clack
cover the longer recovery. Deterministic (fixed seed). Writes 16-bit mono PCM at 44.1 kHz.

usage: make_sound.py <output.wav>
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'assets_dev/engine/audio/shoot blaster01.wav'
RATE = 44100


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 's16le', '-ac', '1', '-ar', str(RATE), '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0


def resample(signal, factor):
    """Play `signal` `factor` times faster (higher pitch, shorter)."""
    positions = np.arange(0.0, len(signal) - 1, factor)
    return np.interp(positions, np.arange(len(signal)), signal)


def one_pole_lowpass(signal, cutoff):
    alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff / RATE)
    out = np.empty_like(signal)
    state = 0.0
    for index, value in enumerate(signal):
        state += alpha * (value - state)
        out[index] = state
    return out


def place(mix, signal, start_seconds, gain):
    start = int(start_seconds * RATE)
    end = min(len(mix), start + len(signal))
    mix[start:end] += signal[:end - start] * gain


def main():
    rng = np.random.default_rng(7)
    shot = decode(SOURCE)
    mix = np.zeros(int(1.0 * RATE))

    # Scatter volley: seven emitters, pitch spread around the stock shot, staggered by a few milliseconds.
    factors = [0.82, 0.88, 0.94, 1.0, 1.06, 1.12, 1.18]
    for index, factor in enumerate(factors):
        delay = 0.004 * index + rng.uniform(0.0, 0.006)
        place(mix, resample(shot, factor), delay, 0.42 - 0.025 * abs(index - 3))

    t = np.arange(int(0.35 * RATE)) / RATE
    # Low thump: falling sine 130 -> 42 Hz.
    frequency = 42.0 + 88.0 * np.exp(-t / 0.05)
    phase = 2.0 * np.pi * np.cumsum(frequency) / RATE
    place(mix, np.sin(phase) * np.exp(-t / 0.09), 0.0, 0.85)
    # Crack: short low-passed noise burst.
    noise = one_pole_lowpass(rng.uniform(-1.0, 1.0, len(t)), 2500.0)
    place(mix, noise * np.exp(-t / 0.025), 0.0, 0.9)

    # Energy whine falling 2600 -> 500 Hz with a fast tremolo, under the volley's tail.
    t = np.arange(int(0.45 * RATE)) / RATE
    frequency = 500.0 + 2100.0 * np.exp(-t / 0.12)
    phase = 2.0 * np.pi * np.cumsum(frequency) / RATE
    whine = np.sin(phase) * (0.6 + 0.4 * np.sin(2.0 * np.pi * 38.0 * t)) * np.exp(-t / 0.16)
    place(mix, whine, 0.03, 0.12)

    # Recharge clack: two metallic clicks (damped high partials) as the emitter bank re-arms.
    t = np.arange(int(0.06 * RATE)) / RATE
    for start, pitch in ((0.56, 1.0), (0.66, 0.8)):
        click = sum(np.sin(2.0 * np.pi * f * pitch * t) * a for f, a in ((1850, 1.0), (3120, 0.6), (4870, 0.35)))
        click += rng.uniform(-1.0, 1.0, len(t)) * 0.5
        place(mix, click * np.exp(-t / 0.012), start, 0.22)

    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.4) / np.tanh(1.4) * 0.92
    fade = int(0.02 * RATE)
    mix[-fade:] *= np.linspace(1.0, 0.0, fade)
    last = np.nonzero(np.abs(mix) > 1e-3)[0][-1] + int(0.02 * RATE)
    mix = mix[:min(last, len(mix))]

    with wave.open(sys.argv[1], 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes((mix * 32767.0).astype('<i2').tobytes())


if __name__ == '__main__':
    main()
