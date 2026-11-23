#!/usr/bin/env python3
"""Piano roll of a reference excerpt (basic-pitch transcription) with a beat grid, to read the melody's shape,
the bass line and the accompaniment pattern by eye.
    python pianoroll.py <wav> <start_s> <seconds> -> work/analysis/<stem>_roll_<start>.png
"""
import sys
from pathlib import Path

import librosa
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyse import transcribe, NOTE_NAMES

HERE = Path(__file__).resolve().parent


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import soundfile as sf
    import tempfile
    path, start, seconds = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    y, sr = librosa.load(path, sr=22050, mono=True, offset=start, duration=seconds)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, y, sr)
        notes = transcribe(tmp.name, seconds)
        _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    fig, ax = plt.subplots(figsize=(22, 9))
    for s, e, p, a in notes:
        if a < 0.2:
            continue
        ax.add_patch(plt.Rectangle((s, p - 0.4), e - s, 0.8, color=plt.cm.viridis(min(1.0, a * 1.4))))
    for i, b in enumerate(beats):
        ax.axvline(b, color="#999" if i % 4 else "#333", lw=0.5 if i % 4 else 1.0)
    lo = min((n[2] for n in notes), default=36) - 1
    hi = max((n[2] for n in notes), default=84) + 1
    ax.set_ylim(lo, hi)
    ax.set_xlim(0, seconds)
    ax.set_yticks(range(lo, hi + 1))
    ax.set_yticklabels([f"{NOTE_NAMES[p % 12]}{p // 12 - 1}" for p in range(lo, hi + 1)], fontsize=6)
    ax.grid(axis="y", lw=0.2)
    ax.set_title(f"{path.stem} {start:g}-{start + seconds:g} s (dark lines every 4 beats)")
    out = HERE / "work" / "analysis" / f"{path.stem}_roll_{int(start)}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=60)
    print(out)


if __name__ == "__main__":
    main()
