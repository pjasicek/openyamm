#!/usr/bin/env python3
"""Checks of the renders: harmony against a reference recording (chroma DTW over 40 s of the reference against
the whole render; the same with the reference shifted 1-11 semitones as the wrong-note baseline), the loop wrap
(level of the last and first half second, the sample jump), level and clipping. Writes work/checks.json.
    python checks.py
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from review_page import REFS, SONGS  # noqa: E402


def chroma(y, sr):
    c = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    return c / (np.linalg.norm(c, axis=0, keepdims=True) + 1e-9)


def match(render, ref):
    y, sr = librosa.load(render, sr=22050, mono=True)
    r, _ = librosa.load(ref, sr=22050, mono=True, offset=5, duration=40)
    a, b = chroma(r, sr), chroma(y, sr)

    def score(x, z):
        _, wp = librosa.sequence.dtw(X=x, Y=z, metric="cosine", subseq=True)
        return float(np.mean([x[:, i] @ z[:, j] for i, j in wp]))
    s0 = score(a, b)
    wrong = [score(np.roll(a, k, axis=0), b) for k in range(1, 12)]
    return s0, float(np.mean(wrong)), max(wrong)


def main():
    out = {}
    listed = [(song, ref) for song, _, _, ref in SONGS]
    listed += [(f"{m.stem.split('_', 1)[0]}/{m.stem.split('_', 1)[1]}", None) for m in sorted((HERE / "out").glob("*.wav"))
               if f"{m.stem.split('_', 1)[0]}/{m.stem.split('_', 1)[1]}" not in {s for s, _ in listed}]
    for song, ref in listed:
        path = HERE / "out" / f"{song.replace('/', '_')}.wav"
        if not path.exists():
            continue
        audio, rate = sf.read(path)
        mono = audio.mean(axis=1)
        half = rate // 2
        db = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
        text = (f"{len(mono) / rate:.0f} s, RMS {db(mono):.1f} dBFS, peak {20 * np.log10(np.abs(audio).max()):.1f}; "
                f"wrap: last 0.5 s {db(mono[-half:]):.1f} dB, first 0.5 s {db(mono[:half]):.1f} dB, "
                f"jump {abs(audio[-1] - audio[0]).max():.3f}")
        if ref and (REFS / f"{ref}.mp3").exists():
            s0, base, best = match(path, REFS / f"{ref}.mp3")
            text += f"; harmony against the recording {s0:.2f} (wrong keys {base:.2f}, best wrong {best:.2f})"
        out[song] = text
        print(song, text, flush=True)
    (HERE / "work" / "checks.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
