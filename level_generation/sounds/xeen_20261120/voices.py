#!/usr/bin/env python3
"""Measure voice takes and pick the set of five designed voices that lie furthest apart (lane AU, D-38).

    work/venv/bin/python voices.py designs            # the Voice Design previews: measures and the best set
    work/venv/bin/python voices.py takes <job> ...    # measures of the takes of TTS or derived jobs

Measures per file: length, the median voice pitch (f0, Hz) and its spread (10th-90th percentile, semitones), the
mean first two formants (F1, F2: the size of the throat), the harmonics-to-noise ratio (HNR, dB: low is breathy or
rasping), the spectral centroid, and a timbre vector: the mean log-mel spectrum (40 bands, 60-8 000 Hz) of the
voiced frames with its overall level removed. The distance between two voices is the RMS difference of their timbre
vectors (dB) plus the pitch difference in semitones scaled by 0.5, so two voices of one timbre but an octave apart
still count as distinct. `designs` tries every combination of one preview per speaker and ranks them by the smallest
distance between any two speakers (then by the mean distance).

Needs the lane's venv (praat-parselmouth, numpy, scipy): `uv venv work/venv && uv pip install praat-parselmouth scipy
pyyaml faster-whisper` (see AUDIO.md (d)).
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import parselmouth
from scipy.io import wavfile
from scipy.signal import stft

HERE = Path(__file__).resolve().parent
SPEAKERS = ['vd_burlock', 'vd_lord_xeen', 'vd_sheltem', 'vd_corak', 'vd_pharaoh']


def mel_filterbank(rate, n_fft, bands=40, low=60.0, high=8000.0):
    def to_mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def to_hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    edges = to_hz(np.linspace(to_mel(low), to_mel(high), bands + 2))
    freqs = np.linspace(0, rate / 2, n_fft // 2 + 1)
    bank = np.zeros((bands, len(freqs)))
    for i in range(bands):
        left, centre, right = edges[i], edges[i + 1], edges[i + 2]
        bank[i] = np.clip(np.minimum((freqs - left) / (centre - left), (right - freqs) / (right - centre)), 0, None)
    return bank


def measure(path):
    rate, data = wavfile.read(path)
    audio = data.astype(np.float64)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio /= 32768.0 if data.dtype == np.int16 else 1.0
    sound = parselmouth.Sound(audio, sampling_frequency=rate)
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=50, pitch_ceiling=500)
    f0 = pitch.selected_array['frequency']
    voiced = f0[f0 > 0]
    formants = sound.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=5000)
    times = pitch.xs()[f0 > 0]
    f1 = np.array([formants.get_value_at_time(1, t) for t in times])
    f2 = np.array([formants.get_value_at_time(2, t) for t in times])
    hnr = sound.to_harmonicity_cc(time_step=0.01, minimum_pitch=50)
    hnr_values = hnr.values[hnr.values > -100]
    n_fft = 1024
    freqs, frame_times, spec = stft(audio, fs=rate, nperseg=n_fft, noverlap=n_fft - 480)
    power = np.abs(spec) ** 2
    mel = np.log10(mel_filterbank(rate, n_fft) @ power + 1e-10) * 10.0
    level = mel.max(axis=0)
    active = level > level.max() - 30.0
    timbre = mel[:, active].mean(axis=1)
    timbre -= timbre.mean()
    centroid = float((freqs[:, None] * power).sum() / max(power.sum(), 1e-12))
    return {
        'seconds': round(len(audio) / rate, 2),
        'f0': round(float(np.median(voiced)), 1) if len(voiced) else 0.0,
        'f0_spread_st': round(float(12 * np.log2(np.percentile(voiced, 90) / np.percentile(voiced, 10))), 1)
        if len(voiced) > 10 else 0.0,
        'f1': round(float(np.nanmean(f1)), 0) if len(f1) else 0.0,
        'f2': round(float(np.nanmean(f2)), 0) if len(f2) else 0.0,
        'hnr': round(float(np.mean(hnr_values)), 1) if len(hnr_values) else 0.0,
        'centroid': round(centroid, 0),
        'timbre': timbre,
    }


def distance(a, b):
    timbre = float(np.sqrt(np.mean((a['timbre'] - b['timbre']) ** 2)))
    pitch = abs(12 * np.log2(max(a['f0'], 1) / max(b['f0'], 1)))
    return timbre + 0.5 * pitch


def row(name, m):
    return (f"{name:<28} {m['seconds']:>5.1f}s f0 {m['f0']:>5.1f} Hz spread {m['f0_spread_st']:>4.1f} st "
            f"F1 {m['f1']:>4.0f} F2 {m['f2']:>5.0f} HNR {m['hnr']:>5.1f} centroid {m['centroid']:>5.0f}")


def designs():
    measured = {}
    for speaker in SPEAKERS:
        # A speaker's later design requests (vd_<speaker>_2 ...) are candidates too.
        for design in [speaker] + sorted(p.name for p in (HERE / 'out').glob(speaker + '_[0-9]')):
            for path in sorted((HERE / 'out' / design).glob('p*.wav')):
                label = path.stem if design == speaker else f'{design[len(speaker) + 1:]}.{path.stem}'
                measured[(speaker, label)] = measure(path)
                print(row(f'{speaker}/{label}', measured[(speaker, label)]))
    options = [[key for key in measured if key[0] == speaker] for speaker in SPEAKERS]
    ranked = []
    for combo in itertools.product(*options):
        pairs = [distance(measured[a], measured[b]) for a, b in itertools.combinations(combo, 2)]
        ranked.append((min(pairs), float(np.mean(pairs)), combo))
    ranked.sort(reverse=True)
    print('\nbest sets (smallest pairwise distance, mean):')
    for low, mean, combo in ranked[:8]:
        print(f'  {low:5.2f} {mean:5.2f}  ' + ' '.join(f'{s[3:]}={p}' for s, p in combo))
    low, mean, combo = ranked[0]
    print('\npairwise distances of the best set:')
    for a, b in itertools.combinations(combo, 2):
        print(f'  {a[0][3:]:>10}/{a[1]} - {b[0][3:]:<10}/{b[1]}: {distance(measured[a], measured[b]):5.2f}')


def takes(jobs):
    for job in jobs:
        for path in sorted((HERE / 'out' / job).glob('v*.wav')):
            print(row(f'{job}/{path.stem}', measure(path)))


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'designs':
        designs()
    elif len(sys.argv) >= 3 and sys.argv[1] == 'takes':
        takes(sys.argv[2:])
    else:
        sys.exit(__doc__)
