"""Per-frame pose tables for the v2 clips from the native fits (system Python).

Keys are the fitted poses at the native frame times (work/v2/fit/<clip>.json, scripts/fit_native.py). Each
parameter is interpolated with a cubic spline through its keys: periodic for the flight loop (native group m183w,
0.9375 s), clamped for the one-shot actions, which start at the standing frame sa and return to it. Minor parameters
that the silhouettes barely constrain (tail, legs, spine, neck roll) are blended halfway toward their clip mean so
fit noise does not become jitter. The body bob comes from the native frames: the vertical translation that aligned
each fitted pose with its native frame (median over the views) relative to the standing frame, in metres.
Clips at 24 fps: Standing/Walking 22 frames, Running 18 (same strokes, faster, leaning 0.08 rad further forward),
Fidget 44 (two strokes, a look to each side in the second), Attack/Cast 21, Hit 21, Death 30 (native order, held
on the corpse from xa), Dead 24 (corpse held).
Writes work/v2/clip_tables.json."""
import json
import numpy as np
from pathlib import Path
from scipy.interpolate import CubicSpline
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dragon_pose as DP
P = Path(__file__).resolve().parents[1]; FIT = P / 'work/v2/fit'
MINOR = ['tail_pitch1', 'tail_pitch2', 'tail_yaw1', 'tail_yaw2', 'fore_upper', 'fore_lower', 'hind_upper', 'hind_lower',
         'spine_pitch', 'spine_yaw', 'neck_roll']
KEYS = DP.NAMES + ['r_' + k for k in DP.WING_KEYS]
FLIGHT = .9375


def load(clip):
    d = json.loads((FIT / f'{clip}.json').read_text()); scale = d['scale']
    keys = []
    sa_dy = np.median([v[0] for v in d['frames'][0]['shift_px'].values()])
    for f in d['frames']:
        p = DP.full(f['pose'])
        for k in DP.WING_KEYS: p.setdefault('r_' + k, p[k])
        dy = np.median([v[0] for v in f['shift_px'].values()])
        p['bob'] = -(dy - sa_dy) / scale
        keys.append((f['time'], f['frame'], p))
    return keys


def table(keys, times, periodic=None, end=None, minor_blend=.5):
    ts = [k[0] for k in keys]; vals = {n: [k[2].get(n, DP.DEFAULT.get(n, 0.)) for k in keys] for n in KEYS + ['bob']}
    if periodic:
        ts = ts + [periodic]
        for n in vals: vals[n] = vals[n] + [vals[n][0]]
    elif end is not None:
        ts = ts + [end]
        for n in vals: vals[n] = vals[n] + [vals[n][0]]
    out = [dict() for _ in times]
    for n, v in vals.items():
        v = np.array(v, float)
        if n in MINOR: v = v * (1 - minor_blend) + v.mean() * minor_blend
        cs = CubicSpline(ts, v, bc_type='periodic' if periodic else 'clamped')
        for i, t in enumerate(times): out[i][n] = float(cs(t))
    return out


flight = load('flight'); attack = load('attack'); hit = load('hit'); death = load('death')
clips = {}
nf = 22; clips['Standing'] = table(flight, [f * FLIGHT / nf for f in range(nf + 1)], periodic=FLIGHT)
clips['Walking'] = clips['Standing']
run = table(flight, [f * FLIGHT / 18 for f in range(19)], periodic=FLIGHT)
for p in run: p['root_pitch'] += .08; p['neck_pitch1'] -= .05
clips['Running'] = run
fid = table(flight, [(f * FLIGHT / nf) % FLIGHT for f in range(2 * nf + 1)], periodic=FLIGHT)
for f, p in enumerate(fid):
    t = f / (2 * nf)
    look = np.sin(np.pi * np.clip((t - .45) / .55, 0, 1)) ** 2 * np.sin(2 * np.pi * np.clip((t - .45) / .55, 0, 1))
    p['head_yaw'] += .30 * look; p['neck_yaw'] += .25 * look; p['jaw'] += .10 * np.sin(np.pi * np.clip((t - .55) / .3, 0, 1))
clips['Fidget'] = fid
clips['Attack'] = table(attack, [f / 24 for f in range(22)], end=.875)[:22]
# the bite (native ad at 0.5 s shows the open maw; silhouettes do not constrain the jaw): open the jaw from 0.30 s,
# widest at 0.5 s, closed by 0.68 s, with a small forward push of the neck
for f, p in enumerate(clips['Attack']):
    t = f / 24; b = np.clip(1 - abs(t - .5) / .18, 0, 1); b = b * b * (3 - 2 * b)
    p['jaw'] = max(p['jaw'], .04 + .40 * b); p['neck_pitch1'] += .12 * b; p['head_pitch'] -= .08 * b
clips['Cast'] = clips['Attack']
clips['Hit'] = table(hit, [f / 24 for f in range(22)], end=.875)[:22]
# death: native keys up to the corpse (xa at 0.9375), then held; the clip author settles it on the floor
dk = [k for k in death if k[1] != 'dd']
dt = [min(f / 24, .9375) for f in range(31)]
clips['Death'] = table(dk, dt)
clips['Dead'] = [dict(clips['Death'][-1]) for _ in range(25)]
# the hit fits swing the wings far forward over the rearing body (sweep -0.57); that tears the membrane root, so the
# sweep is limited to +-0.4 rad
for frames in clips.values():
    for p in frames:
        for k in ('w_sweep', 'r_w_sweep'):
            if k in p: p[k] = float(np.clip(p[k], -.4, .4))
meta = {'flight_keys': [(k[0], k[1]) for k in flight], 'attack_impact_s': .5, 'bob_m': {c: [round(k[2]['bob'], 4) for k in v] for c, v in
        (('flight', flight), ('attack', attack), ('hit', hit), ('death', death))}}
(P / 'work/v2/clip_tables.json').write_text(json.dumps({'meta': meta, 'clips': clips}) + '\n')
print('TABLES', {c: len(v) for c, v in clips.items()}, meta['bob_m'])
