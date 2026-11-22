#!/usr/bin/env python3
"""Listen-by-analysis for the Xeen takes (lane AU): per variant a feature line and a spectrogram sheet per group.

    python3 level_generation/sounds/xeen_20261120/analyze.py [job ids...]     # all processed sfx jobs by default

Writes review/analysis.txt (appended per run is avoided: rewritten for the jobs given) and review/sheets/<group>.png:
one row per job, one column per variant (log-frequency spectrogram 40 Hz-16 kHz over the waveform envelope).

Features: length; punch (loudest 100 ms, dBFS); attack (ms to within 6 dB of the envelope peak); events (rises after
a dip of at least 8 dB); decay (s from the peak until 30 dB down); band shares (<150, 150-600, 600-2.5k, 2.5k-8k,
>8k Hz); flatness (median spectral flatness: 0 tonal, 1 noise); voiced share and median f0 (normalised
autocorrelation over 60-1000 Hz, peak > 0.55); for loops the 2 s level spread.
"""
import sys
import wave
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
RATE = 48000


def read_wav(path):
    with wave.open(str(path)) as handle:
        frames = handle.readframes(handle.getnframes())
        channels = handle.getnchannels()
        rate = handle.getframerate()
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    assert rate == RATE, path
    return audio


def envelope_db(audio, window=0.01):
    size = int(window * RATE)
    count = max(1, len(audio) // size)
    frames = audio[:count * size].reshape(count, size)
    return 10 * np.log10(np.mean(frames ** 2, axis=1) + 1e-12)


def features(audio, loop=False):
    seconds = len(audio) / RATE
    hop = int(0.1 * RATE)
    punch = max((10 * np.log10(np.mean(audio[i:i + hop] ** 2) + 1e-12)
                 for i in range(0, max(1, len(audio) - hop), hop // 4)), default=-120)
    env = envelope_db(audio)
    peak_index = int(np.argmax(env))
    peak = env[peak_index]
    attack = int(np.argmax(env >= peak - 6)) * 10
    below = np.nonzero(env[peak_index:] < peak - 30)[0]
    decay = (below[0] if len(below) else len(env) - peak_index) * 0.01
    # events: a rise of 8 dB over the lowest point since the last event (or the start), reaching within 25 dB of the
    # peak; the next one needs a dip of 8 dB under the high point since then.
    events, low, high, armed = 0, -120.0, -120.0, True
    for value in env:
        if armed:
            low = min(low, value)
            if value > low + 8 and value > peak - 25:
                events += 1
                armed, high = False, value
        else:
            high = max(high, value)
            if value < high - 8:
                armed, low = True, value
    spectrum = np.abs(np.fft.rfft(audio * np.hanning(len(audio)))) ** 2
    freqs = np.fft.rfftfreq(len(audio), 1 / RATE)
    total = spectrum.sum() + 1e-12
    edges = [0, 150, 600, 2500, 8000, RATE / 2]
    bands = [spectrum[(freqs >= a) & (freqs < b)].sum() / total for a, b in zip(edges, edges[1:])]
    centroid = float((freqs * spectrum).sum() / total)
    # frame-wise flatness and pitch
    size, step = 2048, 1024
    flat, voiced, pitches = [], 0, []
    frames = 0
    for start in range(0, len(audio) - size, step):
        frame = audio[start:start + size] * np.hanning(size)
        energy = np.mean(frame ** 2)
        if energy < 10 ** (-45 / 10):
            continue
        frames += 1
        power = np.abs(np.fft.rfft(frame)) ** 2 + 1e-12
        flat.append(np.exp(np.mean(np.log(power))) / np.mean(power))
        corr = np.fft.irfft(power)[:size // 2]
        corr /= corr[0]
        lo, hi = RATE // 800, RATE // 60
        lag = lo + int(np.argmax(corr[lo:hi]))
        if corr[lag] > 0.55 and lo < lag < hi - 1:
            voiced += 1
            pitches.append(RATE / lag)
    result = {
        'len': round(seconds, 2), 'punch': round(float(punch), 1), 'attack_ms': attack, 'events': events,
        'decay_s': round(decay, 2), 'bands': [round(b * 100) for b in bands], 'centroid': int(centroid),
        'flat': round(float(np.median(flat)) if flat else 1.0, 3),
        'voiced': round(voiced / frames, 2) if frames else 0.0,
        'f0': int(np.median(pitches)) if pitches else 0,
    }
    if loop:
        win = 2 * RATE
        levels = [10 * np.log10(np.mean(audio[i:i + win] ** 2) + 1e-12) for i in range(0, len(audio) - win + 1, win)]
        result['spread_db'] = round(float(np.percentile(levels, 90) - np.percentile(levels, 10)), 1) if levels else 0
        result['seam_jump'] = round(float(abs(audio[-1] - audio[0])), 4)
    return result


def colour(value):
    """0..1 to a dark-blue -> orange -> white ramp."""
    stops = [(0.0, (8, 8, 24)), (0.35, (40, 30, 110)), (0.6, (200, 60, 60)), (0.85, (250, 180, 60)),
             (1.0, (255, 255, 230))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if value <= b:
            t = (value - a) / (b - a) if b > a else 0
            return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))
    return stops[-1][1]


LUT = np.array([colour(i / 255) for i in range(256)], dtype=np.uint8)


def spectrogram_tile(audio, width=300, height=120, seconds=None):
    size = 2048
    span = seconds or len(audio) / RATE
    total = int(span * RATE)
    padded = np.zeros(max(total, size) + size, dtype=np.float32)
    padded[:min(len(audio), total)] = audio[:total]
    columns = []
    for x in range(width):
        start = int(x / width * total)
        frame = padded[start:start + size] * np.hanning(size)
        columns.append(np.abs(np.fft.rfft(frame)) ** 2)
    spec = np.array(columns).T
    freqs = np.fft.rfftfreq(size, 1 / RATE)
    targets = np.geomspace(40, 16000, height)[::-1]
    rows = np.array([spec[np.argmin(np.abs(freqs - f))] for f in targets])
    db = 10 * np.log10(rows + 1e-12)
    db = np.clip((db - (db.max() - 70)) / 70, 0, 1)
    image = Image.fromarray(LUT[(db * 255).astype(np.uint8)], 'RGB')
    draw = ImageDraw.Draw(image)
    env = envelope_db(padded[:total], window=span / width)[:width]
    points = [(x, int(height - 2 - np.clip((v + 60) / 60, 0, 1) * (height - 4))) for x, v in enumerate(env)]
    draw.line(points, fill=(120, 255, 120), width=1)
    return image


def main():
    jobs = yaml.safe_load((ROOT / 'jobs.yml').read_text())['jobs']
    wanted = set(sys.argv[1:])
    selected = [j for j in jobs if j.get('kind', 'sfx') == 'sfx' and (not wanted or j['id'] in wanted)]
    lines, groups = [], {}
    for job in selected:
        directory = ROOT / 'out' / job['id']
        variants = sorted(directory.glob('v[0-9]*.wav'), key=lambda p: int(p.stem[1:])) if directory.exists() else []
        if not variants:
            continue
        lines.append(f"== {job['id']} ({job.get('duration')} s asked{', loop' if job.get('loop') else ''})")
        tiles = []
        longest = max(len(read_wav(v)) for v in variants) / RATE
        for path in variants:
            audio = read_wav(path)
            f = features(audio, loop=bool(job.get('loop')))
            lines.append(f"  {path.name}: " + ' '.join(f'{k}={v}' for k, v in f.items()))
            tiles.append((path.name, spectrogram_tile(audio, seconds=min(longest, 30))))
        groups.setdefault(job.get('group', 'misc'), []).append((job['id'], tiles))
    (ROOT / 'review').mkdir(exist_ok=True)
    report = ROOT / 'review' / 'analysis.txt'
    report.write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    sheets = ROOT / 'review' / 'sheets'
    sheets.mkdir(parents=True, exist_ok=True)
    for group, rows in groups.items():
        columns = max(len(t) for _, t in rows)
        tile_w, tile_h, label = 300, 120, 16
        sheet = Image.new('RGB', (columns * (tile_w + 6) + 6, len(rows) * (tile_h + label + 6) + 6), (30, 30, 30))
        draw = ImageDraw.Draw(sheet)
        for r, (job_id, tiles) in enumerate(rows):
            y = 6 + r * (tile_h + label + 6)
            for c, (name, tile) in enumerate(tiles):
                x = 6 + c * (tile_w + 6)
                draw.text((x, y), f'{job_id} {name}', fill=(230, 230, 230))
                sheet.paste(tile, (x, y + label))
        safe = ''.join(ch if ch.isalnum() else '_' for ch in group).strip('_').lower()
        sheet.save(sheets / f'{safe}.png')
        print('sheet:', sheets / f'{safe}.png')


if __name__ == '__main__':
    main()
