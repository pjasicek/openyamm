#!/usr/bin/env python3
"""Describe reference music so it can be prompted: tempo, key, chords per bar, the melody's first phrases
(basic-pitch transcription, top line), brightness and level. (Zero-shot CLAP instrument tags were tried and
dropped: with transformers 5 every track got the same tags.)

Run with a venv that has librosa, soundfile, matplotlib and basic-pitch (onnxruntime):
    python analyse.py work/ref/<name>.wav [...]   -> work/analysis/<name>.json and .md
The reference recordings stay in work/ (git-ignored); only this script and the prompts are tracked.
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "work" / "analysis"
NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])



def estimate_key(chroma_mean):
    best = None
    for tonic in range(12):
        for mode, profile in (("major", MAJOR), ("minor", MINOR)):
            r = np.corrcoef(chroma_mean, np.roll(profile, tonic))[0, 1]
            if best is None or r > best[0]:
                best = (r, f"{NOTE_NAMES[tonic]} {mode}")
    ranked = []
    for tonic in range(12):
        for mode, profile in (("major", MAJOR), ("minor", MINOR)):
            ranked.append((float(np.corrcoef(chroma_mean, np.roll(profile, tonic))[0, 1]), f"{NOTE_NAMES[tonic]} {mode}"))
    ranked.sort(reverse=True)
    return ranked[:3]


TRIADS = []
for root in range(12):
    for quality, intervals in (("", (0, 4, 7)), ("m", (0, 3, 7)), ("dim", (0, 3, 6)), ("sus4", (0, 5, 7))):
        TRIADS.append((NOTE_NAMES[root] + quality, {(root + i) % 12 for i in intervals}, root))


def bar_chord(weights):
    """weights: 12 pitch-class weights (duration * velocity, bass-weighted)."""
    if weights.sum() <= 0:
        return "-"
    best = max(TRIADS, key=lambda t: sum(weights[p] for p in t[1]) - 0.5 * sum(
        weights[p] for p in range(12) if p not in t[1]) + 0.15 * weights[t[2]])
    return best[0]


def transcribe(path, seconds):
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import predict
    import soundfile as sf
    import tempfile
    y, sr = librosa.load(path, sr=22050, mono=True, duration=seconds)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, y, sr)
        model_path = Path(ICASSP_2022_MODEL_PATH)
        onnx = model_path.with_suffix(".onnx") if model_path.suffix != ".onnx" else model_path
        _, _, notes = predict(tmp.name, onnx if onnx.exists() else model_path,
                              onset_threshold=0.55, frame_threshold=0.3, minimum_note_length=80)
    # (start, end, pitch, amplitude, bends)
    return [(float(s), float(e), int(p), float(a)) for s, e, p, a, *_ in notes]


def melody_and_chords(notes, beat_times, beats_per_bar=4, bars=16):
    if len(beat_times) < 8:
        return [], []
    step = float(np.median(np.diff(beat_times)))
    start = float(beat_times[0])
    # Top line on an eighth-note grid.
    grid = step / 2
    cells = int(min(bars * beats_per_bar * 2, (notes[-1][1] - start) / grid)) if notes else 0
    top = []
    for i in range(cells):
        t0 = start + i * grid
        t1 = t0 + grid
        sounding = [n for n in notes if n[0] < t1 - grid * 0.25 and n[1] > t0 + grid * 0.25 and n[3] > 0.25
                    and n[2] >= 55]
        if not sounding:
            top.append(None)
            continue
        onset_here = [n for n in sounding if t0 - grid * 0.3 <= n[0] < t1 - grid * 0.3]
        pick = max(sounding, key=lambda n: n[2])
        top.append((pick[2], bool(onset_here) and pick in onset_here))
    phrase = []
    for cell in top:
        if cell is None:
            if phrase and phrase[-1][0] == "r":
                phrase[-1][1] += 1
            else:
                phrase.append(["r", 1])
        elif phrase and phrase[-1][0] == cell[0] and not cell[1]:
            phrase[-1][1] += 1
        else:
            phrase.append([cell[0], 1])
    melody = []
    for pitch, eighths in phrase:
        name = "rest" if pitch == "r" else f"{NOTE_NAMES[pitch % 12]}{pitch // 12 - 1}"
        melody.append(f"{name}:{eighths / 2:g}")
    chords = []
    bar_len = step * beats_per_bar
    for b in range(bars):
        t0 = start + b * bar_len
        t1 = t0 + bar_len
        w = np.zeros(12)
        low = 200
        for s, e, p, a in notes:
            ov = min(e, t1) - max(s, t0)
            if ov > 0:
                w[p % 12] += ov * a * (1.6 if p < 55 else 1.0)
                low = min(low, p)
        chords.append(bar_chord(w))
    return melody, chords



def save_images(y, sr, chroma, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import librosa.display
    n = sr * 60
    fig, ax = plt.subplots(2, 1, figsize=(16, 7))
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y[:n], n_fft=2048, hop_length=512)), ref=np.max)
    librosa.display.specshow(S, sr=sr, hop_length=512, x_axis="time", y_axis="log", ax=ax[0])
    ax[0].set_title("spectrogram, first 60 s")
    librosa.display.specshow(chroma[:, :librosa.time_to_frames(60, sr=sr)], sr=sr, x_axis="time", y_axis="chroma",
                             ax=ax[1])
    ax[1].set_title("chroma, first 60 s")
    fig.tight_layout()
    fig.savefig(out, dpi=70)
    plt.close(fig)


def analyse(path):
    path = Path(path)
    y, sr = librosa.load(path, sr=22050, mono=True, duration=240)
    dur_total = librosa.get_duration(path=str(path))
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    keys = estimate_key(chroma.mean(axis=1))
    rms = librosa.feature.rms(y=y)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    onset_rate = len(librosa.onset.onset_detect(y=y, sr=sr)) / (len(y) / sr)
    sections = []
    for t0 in range(0, int(len(y) / sr) - 20, 30):
        seg = chroma[:, librosa.time_to_frames(t0, sr=sr):librosa.time_to_frames(t0 + 30, sr=sr)]
        sections.append(f"{t0}s {estimate_key(seg.mean(axis=1))[0][1]}")
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_frames = librosa.time_to_frames(beats, sr=sr)
    beat_strength = onset_env[beat_frames[beat_frames < len(onset_env)]]
    meter = {}
    for m in (3, 4):
        if len(beat_strength) > 4 * m:
            phases = [float(beat_strength[i::m].mean()) for i in range(m)]
            meter[m] = round(max(phases) / (np.mean(phases) + 1e-6), 3)
    save_images(y, sr, chroma, OUT / f"{path.stem}.png")
    notes = transcribe(path, 120)
    melody, chords = melody_and_chords(notes, beats[beats < 120])
    pitches = [n[2] for n in notes if n[3] > 0.3]
    result = {
        "file": path.name,
        "duration_s": round(dur_total, 1),
        "tempo_bpm": round(tempo, 1),
        "key_candidates": [(k, round(r, 3)) for r, k in keys],
        "level_db_p10_p50_p90": [round(float(np.percentile(db, q)), 1) for q in (10, 50, 90)],
        "brightness_hz_median": round(float(np.median(cent))),
        "onsets_per_s": round(onset_rate, 2),
        "pitch_range": [librosa.midi_to_note(min(pitches)), librosa.midi_to_note(max(pitches))] if pitches else None,
        "chords_first_16_bars": chords,
        "key_by_30s": sections,
        "downbeat_contrast_by_meter": meter,
        "melody_first_16_bars": melody,
    }
    return result


def to_md(r):
    lines = [f"## {r['file']} ({r['duration_s']} s)", "",
             f"- tempo {r['tempo_bpm']} bpm; key {', '.join(f'{k} ({c})' for k, c in r['key_candidates'])}",
             f"- level p10/p50/p90 {r['level_db_p10_p50_p90']} dB; brightness {r['brightness_hz_median']} Hz; "
             f"onsets {r['onsets_per_s']}/s; range {r['pitch_range']}",
             f"- key by 30 s: {', '.join(r['key_by_30s'])}; downbeat contrast 3 vs 4: {r['downbeat_contrast_by_meter']}",
             f"- chords (bars 1-16): {' | '.join(r['chords_first_16_bars'])}",
             f"- melody top line (note:beats): {' '.join(r['melody_first_16_bars'][:80])}"]
    return "\n".join(lines) + "\n"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[1:]:
        r = analyse(arg)
        stem = Path(arg).stem
        (OUT / f"{stem}.json").write_text(json.dumps(r, indent=1))
        (OUT / f"{stem}.md").write_text(to_md(r))
        print(to_md(r), flush=True)


if __name__ == "__main__":
    main()
