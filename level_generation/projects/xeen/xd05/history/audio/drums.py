"""Three looping war-drum layers for XD-05 (synthesised, our own): great drum, signal drum, spirit drum.

Each is a seamless loop (hits laid on a circular buffer, reverb by circular convolution), mono 22050 Hz 16-bit.
python3 drums.py <out dir>
"""
import sys, wave
import numpy as np

SR = 22050
rng = np.random.default_rng(5)


def hit(f0, f1, decay, length, noise=0.3, noise_decay=0.02, bright=0.0):
    t = np.arange(int(length * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.05)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) + 0.35 * np.sin(1.5 * phase + 0.3) * np.exp(-t / (decay * 0.5))
    body *= np.exp(-t / decay)
    n = rng.standard_normal(len(t)) * np.exp(-t / noise_decay)
    # low-passed thump noise
    k = max(1, int(SR / 900))
    n = np.convolve(n, np.ones(k) / k, mode='same')
    out = body + noise * n
    if bright:
        out += bright * rng.standard_normal(len(t)) * np.exp(-t / 0.008)
    return out / np.max(np.abs(out))


def place(buf, sound, at, gain):
    i = int(at * SR) % len(buf)
    for start in range(0, len(sound)):
        pass
    n = len(sound)
    idx = (np.arange(n) + i) % len(buf)
    np.add.at(buf, idx, gain * sound)


def reverb(buf, seconds, mix):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / (seconds / 4))
    ir[:int(0.015 * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(buf)
    wet = np.real(np.fft.ifft(np.fft.fft(buf, L) * np.fft.fft(np.pad(ir, (0, max(0, L - n)))[:L], L)))
    return buf + mix * wet


def write(path, buf, peak):
    buf = buf / np.max(np.abs(buf)) * peak
    data = (buf * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


def great():
    beat = 60 / 72
    L = 8 * beat
    buf = np.zeros(int(L * SR))
    boom = hit(95, 48, 0.55, 1.6, noise=0.5, noise_decay=0.03)
    soft = hit(80, 50, 0.35, 1.2, noise=0.3, noise_decay=0.02)
    for b, g in [(0, 1.0), (2, 0.55), (3, 0.9), (4, 1.0), (6, 0.55), (6.5, 0.5), (7, 0.9)]:
        place(buf, boom if g > 0.8 else soft, b * beat, g)
    return reverb(buf, 1.6, 0.6), 0.9


def signal():
    beat = 60 / 132
    L = 16 * beat
    buf = np.zeros(int(L * SR))
    tom = hit(190, 120, 0.18, 0.7, noise=0.4, noise_decay=0.012, bright=0.15)
    for b in [0, 1, 2, 3, 3.5, 6, 7, 8, 9, 10, 11, 11.5, 14]:
        place(buf, tom, b * beat, 1.0 if b in (0, 8) else 0.7)
    return reverb(buf, 1.2, 0.5), 0.75


def spirit():
    beat = 60 / 96
    L = 12 * beat
    buf = np.zeros(int(L * SR))
    frame = hit(260, 170, 0.12, 0.6, noise=0.6, noise_decay=0.01, bright=0.3)
    for b, g in [(0, 1.0), (1.5, 0.6), (2, 0.8), (4, 1.0), (5.5, 0.6), (6, 0.8), (7, 0.5), (8, 1.0), (9.75, 0.6), (10, 0.8)]:
        place(buf, frame, b * beat, g)
    # bone rattle: short noise grains after some hits
    for b in [0.5, 4.5, 8.5, 11]:
        for k in range(14):
            grain = rng.standard_normal(int(0.012 * SR)) * np.hanning(int(0.012 * SR))
            hp = np.diff(grain, prepend=0)
            place(buf, hp, b * beat + k * 0.02 + rng.uniform(0, 0.01), 0.35 * np.exp(-k / 6))
    return reverb(buf, 1.0, 0.45), 0.7


out = sys.argv[1]
for name, fn in [('xodrumgr', great), ('xodrumsg', signal), ('xodrumsp', spirit)]:
    buf, peak = fn()
    write(f'{out}/{name}.wav', buf, peak)
    print(name, round(len(buf) / SR, 2), 's')
