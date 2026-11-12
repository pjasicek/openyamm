#!/usr/bin/env python3
"""Follow-up 2 (2026-11-12, arms hanging away from the body): per clip and side, at 24 fps, the gap from the hand (hand and finger
vertices) to the rest of the body (skirt, bodice, belt: every face not on an arm), and from the elbow region (forearm vertices within
6 cm of the elbow joint) to the bodice/skirt. Reports min and median over the clip (cm). Args: <glb> [clips]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb = sys.argv[1]; want = sys.argv[2].split(',') if len(sys.argv) > 2 else None
m = Model(Glb(glb)); prims = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
offs = np.cumsum([0] + [len(p['positions']) for p in prims]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(prims, offs)])
n_p = len(prims)
def allpos(w): return np.concatenate([r[0] for r in m.skinned_positions(w)][:n_p])
ARM = ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Elbow', 'Wrist', 'Shoulder')
HAND = ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Finger')
armw = np.zeros(len(J)); side = {}
for s in 'LR':
    a = [i for i, n in enumerate(jn) if f' {s} ' in n and any(k in n for k in ARM)]
    h = [i for i, n in enumerate(jn) if f' {s} ' in n and any(k in n for k in HAND) and 'Forearm' not in n]
    fa = [i for i, n in enumerate(jn) if f' {s} ' in n and 'Forearm' in n]
    aw = (np.isin(J, a) * W).sum(1); armw += aw
    side[s] = dict(hand=np.where((np.isin(J, h) * W).sum(1) > 0.5)[0], fore=np.where((np.isin(J, fa) * W).sum(1) > 0.5)[0],
                   elbow=jn.index(f'FHP {s} Forearm'))
body = np.where((armw[tri] < 0.3).all(1))[0]
# the head/hair are not in the way of a hanging arm; keep bodice, belt, skirt (everything under the neck)
R0 = allpos(m.world({}))
body = body[R0[tri[body]].mean(1)[:, 1] < R0[:, 1].max() * 0.0 + np.percentile(R0[:, 1], 85)]


def gap(P, Q):
    tr = P[tri[body]]; c = tr.mean(1)
    _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9)
    for k in range(8):
        i = ids[:, k]; q, _b = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); best = np.minimum(best, np.linalg.norm(q - Q, axis=1))
    return best


for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    T = np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 24)
    out = {s: dict(h=[], e=[]) for s in 'LR'}
    for t in T:
        w = m.world(m.sample(clip, float(t))); P = allpos(w)
        for s in 'LR':
            out[s]['h'].append(gap(P, P[side[s]['hand']]).min())
            el = w[m.joints[side[s]['elbow']]][:3, 3]; fv = side[s]['fore']; fv = fv[np.linalg.norm(P[fv] - el, axis=1) < 0.06]
            out[s]['e'].append(gap(P, P[fv]).min() if len(fv) else np.nan)
    txt = '  '.join(f"{s}: hand min {100 * np.min(out[s]['h']):5.1f} med {100 * np.median(out[s]['h']):5.1f}  elbow min "
                    f"{100 * np.nanmin(out[s]['e']):5.1f} med {100 * np.nanmedian(out[s]['e']):5.1f}" for s in 'LR')
    print(f'{clip:9} {txt}', flush=True)
