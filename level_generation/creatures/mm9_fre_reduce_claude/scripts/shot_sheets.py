#!/usr/bin/env python3
"""Viewer shots (review/shots[_<clip>]/<inst|red>_<tier>/<tier... name>.png, shots.sh) -> side-by-side sheets, installed above reduced:
face (every tier, with the per-shot pixel difference printed), body, arms from behind, arms from the front (per tier).
Usage: shot_sheets.py <tag> [shots dir]  -> review/sheet_{face,body,back,arms}_<tag>[_<tier>].png"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; S = Path(sys.argv[2] if len(sys.argv) > 2 else 'review/shots'); tiers = 'a'
LB = dict(f0='face front', f1='face 3/4', f2='profile L', f3='profile R', f4='low 3/4', f5='party', f6='Talk', f7='back of head', f8='back 3/4 head',
          b0='Standing front', b1='Standing 3/4', b2='Standing back', b3='Walking 3/4', b4='Talk 3/4', b5='Death 3/4',
          k0='back', k1='low back', k2='elbow back L', k3='elbow back R', k4='back 3/4 L', k5='back 3/4 R', k6='hem back L', k7='hem back R',
          a0='arms 3/4 L', a1='arms 3/4 R', a2='low 3/4 L', a3='low 3/4 R', a4='torso front', a5='torso 3/4',
          c0='hand L 3/4', c1='hand R 3/4', c2='hand L side', c3='hand R side', c4='Talk hand R', c5='hem front', c6='braid', c7='skirt back')
def find(k, t, s):
    d = S / f'{k}_{t}'; c = sorted(d.glob(f'*{s}*.png')) if d.exists() else []
    c = [x for x in c if x.stem == s or x.stem.endswith('_' + s) or x.stem.startswith(s + '_')]
    return Image.open(c[0]).convert('RGB') if c else None
W = 380
def sheet(name, shots, per_tier, diff=False):
    rows = [(t, k) for t in tiers for k in ('inst', 'red')]
    groups = [[r for r in rows if r[0] == t] for t in tiers] if per_tier else [rows]
    for gi, grp in enumerate(groups):
        ims = [find(k, t, s) for t, k in grp for s in shots]
        if not any(ims): continue
        H = int(W * 1060 / 1440)
        sh = Image.new('RGB', (W * len(shots), (H + 20) * len(grp)), (25, 25, 25)); d = ImageDraw.Draw(sh)
        for r, (t, k) in enumerate(grp):
            for i, s in enumerate(shots):
                a = find(k, t, s)
                if a is None: continue
                sh.paste(a.resize((W, H)), (i * W, r * (H + 20) + 20))
                d.text((i * W + 4, r * (H + 20) + 4), f'{t} {"installed" if k == "inst" else tag} {LB[s]}', fill=(255, 220, 120))
        out = f'review/sheet_{name}_{tag}' + (f'_{tiers[gi]}' if per_tier else '') + '.png'; sh.save(out); print('SHEET', out)
    if diff:
        for t in tiers:
            for s in shots:
                a, b = find('inst', t, s), find('red', t, s)
                if a is None or b is None: continue
                a, b = np.asarray(a, float), np.asarray(b, float); h, w = a.shape[:2]
                box = (slice(int(h * 0.1), int(h * 0.75)), slice(int(w * 0.3), int(w * 0.7)))
                dd = np.abs(a - b).max(-1)
                print(f'DIFF {t} {LB[s]}: whole >8: {(dd > 8).mean() * 100:.2f} %, centre box >8: {(dd[box] > 8).mean() * 100:.2f} %, max {dd.max():.0f}')
                Image.fromarray(np.clip(dd * 4, 0, 255).astype(np.uint8)).save(f'review/diff_{tag}_{t}_{s}.png')
sheet('face', ['f0', 'f1', 'f2', 'f3', 'f4', 'f6', 'f7', 'f8', 'f5'], False, diff=True)
sheet('body', ['b0', 'b1', 'b2', 'b3', 'b4', 'b5'], True)
sheet('back', ['k0', 'k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7'], True)
sheet('arms', ['a0', 'a1', 'a2', 'a3', 'a4', 'a5'], True)
sheet('close', ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7'], True, diff=True)
