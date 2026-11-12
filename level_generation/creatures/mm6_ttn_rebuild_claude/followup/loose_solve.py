#!/usr/bin/env python3
"""Loose fist (walk/run/death carry, follow-up 2026-11-11): fingers at FRAC of the way from 'relax' to the side's
solved 'fist@<side>' (finger_poses.json), thumb solved so it rests against the index without entering it or the palm
(fist_solve.py's depth test), near the same blend of the two thumbs. Writes poses 'loose@Left'/'loose@Right'.
Usage: loose_solve.py <splice glb> [frac]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fist_solve as fs
HERE = Path(__file__).resolve().parents[1]
glb = sys.argv[1]; FRAC = float(sys.argv[2]) if len(sys.argv) > 2 else 0.55
cfgp = HERE / 'scripts/finger_poses.json'; cfg = json.load(open(cfgp)); P = cfg['poses']
signs = json.load(open(Path(glb).with_suffix('.json')))['spread_signs']


arr = fs.pose_array
for side in ('Left', 'Right'):
    h = fs.Hand(glb, side, signs)
    rel, fist = arr(P['relax']), arr(P[f'fist@{side}'])
    base = rel + FRAC * (fist - rel)

    def cost(th):
        p = base.copy(); p[12:] = th; m = h.metrics(p)
        c = sum(max(0.0, m['pairs'][k] - 0.1) ** 2 for k in ('TI', 'IT', 'TM', 'MT', 'TH')) * 10
        g = m['_thumb'][0] * 100
        c += max(0.0, 0.2 - g) ** 2 + max(0.0, g - 1.5) ** 2 * 0.3
        c += 1e-3 * float(((th - base[12:]) ** 2).sum())
        return c
    r = minimize(cost, base[12:], method='Powell', bounds=[(-40, 30), (0, 95), (0, 60), (0, 60)],
                 options={'maxfev': 600, 'xtol': 0.5})
    p = base.copy(); p[12:] = np.round(r.x, 1); m = h.metrics(p)
    print('LOOSE', side, 'thumb', p[12:].tolist(), {k: v for k, v in m['pairs'].items() if v > 0}, 'thumb gap', m['thumb_gap_cm'])
    P[f'loose@{side}'] = {'fingers': [0, 0, 0], 'per_finger': {f: np.round(p[k * 3:k * 3 + 3], 1).tolist()
                          for k, f in enumerate(fs.F[1:])}, 'thumb': p[12:].tolist(),
                          '_solved': f'followup/loose_solve.py: fingers {FRAC} relax -> fist@{side}, thumb solved'}
json.dump(cfg, open(cfgp, 'w'), indent=1)
