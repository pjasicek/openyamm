#!/usr/bin/env python3
"""Fit the shell colour (species shell.value, per LOD and channel) so that each LOD's mean colour matches the installed
model's (gate.py renders; half the mean over the three gate views, half the eye view): one grey factor per LOD
(0.3-3), by the secant method on the luminance of the difference: compose.py + gate.py per step (shell.npz unchanged).
Writes the fitted value into species/<id>.json. Usage: tune.py <id> [steps]"""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

tid = sys.argv[1]; steps = int(sys.argv[2]) if len(sys.argv) > 2 else 4
HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(common.HERE, 'species', f'{tid}.json')


def run(value):
    raw = json.load(open(path)); raw.setdefault('shell', {})['value'] = np.round(value, 3).tolist()
    json.dump(raw, open(path, 'w'), indent=1)
    subprocess.run([sys.executable, os.path.join(HERE, 'compose.py'), tid], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, os.path.join(HERE, 'gate.py'), tid], check=True, stdout=subprocess.DEVNULL)
    rep = json.load(open(os.path.join(common.HERE, 'work', tid, 'gate.json'))); g = rep['gates']; r = rep['renders']
    # half the mean over the three gate views, half the eye view (the LOD steps are judged at eye level)
    eye = [np.array(r['new'][str(l)]['eye']['mean']) - np.array(r['inst'][str(l)]['eye']['mean']) for l in range(3)]
    we = [0.5, 0.5, 0.75]                     # LOD2 leans on the eye view: its impostor step is judged there
    return np.array([(1 - we[l]) * np.array(g[f'LOD{l}']['colour_delta']) + we[l] * eye[l] for l in range(3)])


spec = common.load(tid)
# one grey factor per LOD (the shell keeps the hue of the cards it replaces over the impostor texture; per-channel
# factors pushed the hue to blue-grey where little shell shows), fitted on the luminance of the colour difference
LUM = np.array([0.2126, 0.7152, 0.0722])
v0 = spec['shell']['value']
v = np.array([np.mean(x) for x in v0], float) if isinstance(v0, list) and isinstance(v0[0], list) else \
    np.ones(3) * float(np.mean(v0))
v = np.clip(v, 0.3, 3.0)
tried = []


def expand(x):
    return np.repeat(np.asarray(x, float)[:, None], 3, 1)


def score(delta):
    return float(np.abs(delta).max())


d1 = run(expand(v)); tried.append((score(d1), v.copy()))
l1 = d1 @ LUM
print('TUNE', tid, 'value', v.round(3).tolist(), 'delta', d1.round(2).tolist())
v2 = np.clip(v * np.where(l1 < 0, 1.25, 0.8), 0.3, 3.0)
for _ in range(steps):
    if np.abs(l1).max() < 0.4:
        break
    d2 = run(expand(v2)); tried.append((score(d2), v2.copy())); l2 = d2 @ LUM
    print('TUNE', tid, 'value', v2.round(3).tolist(), 'delta', d2.round(2).tolist())
    slope = np.where(np.abs(l2 - l1) > 1e-3, (v2 - v) / (l2 - l1), -0.05)
    nxt = np.clip(v2 - l2 * slope, 0.3, 3.0)
    v, l1, v2 = v2, l2, nxt
best = min(tried, key=lambda t: t[0])[1]
final = run(expand(best))
print('TUNE', tid, 'final value', best.round(3).tolist(), 'delta', final.round(2).tolist())
