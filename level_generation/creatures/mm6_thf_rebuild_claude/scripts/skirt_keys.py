#!/usr/bin/env python3
"""Tunic skirt follows the thighs (overnight gate: thighs must not pass through the skirt in Walking and Running). A closed ring on six hinge
bones `Skirt_*` at the belt, children of Bip01 Spine (the thighs' parent), weighted smoothly round the ring and by height (rig_guard.py).
Per key, in the Spine frame: pants points inside a hinge's sector and within the skirt's reach give the least swing about the hinge that keeps them
MARGIN under the cloth (closed form: atan of radial excess over depth). Curves: running maximum (HOLD s) and Gaussian (SIGMA s; one-shots twice), circular
on loops, on the clip's own keys, never per frame. Side sectors take a share of their neighbours so the ring rises as one. Body channels are not touched.
Args: <in glb> <out glb> <report json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT, REP = sys.argv[1:4]
MARGIN, HOLD, SIGMA, MAXDEG, SKIRT_LEN, SECTOR = 0.025, 0.085, 0.035, 62.0, 0.27, 0.62   # MM6 thief: jerkin skirt 25 cm below the hinges
CLIP_MARGIN = {}      # the two clips with one fast knee drive; the helper bands fill the thigh there
LOOPS = ('Standing', 'Walking', 'Running', 'Walk2', 'Jog')
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SFL', 'Skirt_SBL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SBR', 'Skirt_SFR']
NB = {k: ((k + 1) % 8, (k + 7) % 8) for k in range(8)}
g = Glb(Path(IN)); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]
jn = [names[j] for j in m.joints]
PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
def allpos(w): return np.vstack([x[0] for x, p in zip(m.skinned_positions(w), m.primitives) if p in PR]) if False else np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
SP = names.index('Bip01 Spine')
w0 = m.world({})
S0i = np.linalg.inv(w0[SP])
rest = allpos(w0)
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
legb = [i for i, n in enumerate(jn) if 'Thigh' in n or 'Calf' in n]
legw = np.isin(J, legb) * W
legv = np.where(legw.sum(1) > 0.5)[0]
print('leg verts', len(legv))
hinge = {}
for k, n in enumerate(RING):
    i = names.index(n)
    p = w0[i][:3, 3]
    h = (S0i @ np.r_[p, 1])[:3]                                   # hinge in the Spine frame
    hinge[n] = dict(i=i, p=h, wp=p)
spine_up = S0i[:3, :3] @ np.array([0, 1.0, 0])                     # glTF up at rest, in the Spine frame
cen = np.mean([hinge[n]['wp'] for n in RING], 0)
for n in RING:
    d = hinge[n]['wp'] - cen; d[1] = 0; d /= np.linalg.norm(d)
    if n in ('Skirt_FR', 'Skirt_FL', 'Skirt_BL', 'Skirt_BR'):                         # front and back rise straight fore and aft, not diagonally
        d = np.array([0, 0, np.sign(d[2])])
    hinge[n]['n'] = S0i[:3, :3] @ d
    hinge[n]['ax'] = np.cross(-spine_up, hinge[n]['n'])            # +angle swings the hanging cloth toward n (right-handed about ax)
    hinge[n]['ax'] /= np.linalg.norm(hinge[n]['ax'])
    wd = hinge[n]['wp'] - cen; wd[1] = 0; wd /= np.linalg.norm(wd)
    hinge[n]['sec'] = S0i[:3, :3] @ wd


# rest skirt surface per hinge: outer radial of the cloth at each depth under the hinge
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
sv = np.where((np.isin(J, sk) * W).sum(1) > 0.01)[0]
restS = (S0i @ np.c_[rest, np.ones(len(rest))].T).T[:, :3][sv]
cS = np.mean([hinge[x]['p'] for x in RING], 0)
for nm in RING:
    H = hinge[nm]
    v = restS - H['p']; dep = -(v @ spine_up); rad = v @ H['n']
    sc = (restS - cS) - np.outer((restS - cS) @ spine_up, spine_up); sn = np.linalg.norm(sc, axis=1)
    ok = (sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR)
    bins = np.linspace(0.0, SKIRT_LEN, 9); surf = np.zeros(8)
    for i in range(8):
        m_ = ok & (dep >= bins[i]) & (dep < bins[i + 1])
        surf[i] = rad[m_].max() if m_.any() else np.nan
    idx = np.where(~np.isnan(surf))[0]
    H['surf'] = (0.5 * (bins[:-1] + bins[1:]), np.interp(np.arange(8), idx, surf[idx]))


def rot_q(ax, a):
    s = np.sin(a / 2)
    return np.array([ax[0] * s, ax[1] * s, ax[2] * s, np.cos(a / 2)])


def needs(y):
    """y: leg points in the Spine frame; returns the swing per hinge (radians)."""
    out = np.zeros(8)
    for k, nm in enumerate(RING):
        H = hinge[nm]
        c = np.mean([hinge[x]['p'] for x in RING], 0)
        v = y - H['p']
        depth = -(v @ spine_up)
        rad = v @ H['n']
        sc = (y - c) - np.outer((y - c) @ spine_up, spine_up)
        sn = np.linalg.norm(sc, axis=1)
        ok = (sn > 1e-6) & (depth > 0.01) & ((sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR)) & (np.hypot(depth, rad) < SKIRT_LEN + 0.03)
        if ok.any():
            R = np.interp(depth[ok], H['surf'][0], H['surf'][1])
            a = np.arctan2(rad[ok] + MARGIN, depth[ok]) - np.arctan2(R, depth[ok])
            out[k] = max(0.0, float(a.max()))
    return out


yr = (S0i @ np.c_[rest[legv], np.ones(len(legv))].T).T[:, :3]
A0 = needs(yr)
print('rest need deg', np.round(np.degrees(A0), 1))
rep = {}
new_tracks = {}
for an in doc['animations']:
    clip = an['name']
    if clip == 'Dead': continue
    MARGIN = CLIP_MARGIN.get(clip, 0.03)
    T = np.array(sorted(m.clip_times(clip))); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1); loop = clip in LOOPS
    A = np.zeros((n, 8))
    for f, t in enumerate(T):
        w = m.world(m.sample(clip, float(t)))
        x = allpos(w)[legv]
        Si = np.linalg.inv(w[SP]); y = (Si @ np.c_[x, np.ones(len(x))].T).T[:, :3]
        A[f] = np.maximum(needs(y) - 0.45 * A0, 0)
    A = np.clip(A, 0, np.radians(MAXDEG))
    mode = 'wrap' if loop else 'nearest'
    sz = max(1, int(round(2 * HOLD / dt)) | 1)
    S = np.stack([gaussian_filter1d(maximum_filter1d(A[:, k], sz, mode=mode), (SIGMA if loop else (1.3 if clip == 'Death' else 2) * SIGMA) / dt, mode=mode) for k in range(8)], 1)
    S2 = S.copy()
    for k, (a, b) in NB.items():
        S2[:, k] = np.maximum(S[:, k], 0.62 * np.maximum(S[:, a], S[:, b]))
    if not loop:
        e = np.clip(T / 0.15, 0, 1); e = e * e * (3 - 2 * e)
        if clip != 'CowerEnd':          # the cower phases (script clips, 2026-10-31): CowerEnd starts crouched, CowerStart ends crouched
            S2 = S2 * e[:, None]
        if clip not in ('Death', 'CowerStart'):
            e2 = np.clip((T[-1] - T) / 0.2, 0, 1); e2 = e2 * e2 * (3 - 2 * e2); S2 = S2 * e2[:, None]
    new_tracks[clip] = (T, S2)
    rep[clip] = {RING[k]: round(float(np.degrees(S2[:, k].max())), 1) for k in range(8)}
    print(clip, rep[clip], flush=True)
# Dead holds Death's last
T, S2 = new_tracks['Death']
new_tracks['Dead'] = (np.array(sorted(m.clip_times('Dead'))), None)
for an in doc['animations']:
    clip = an['name']
    T, S2 = new_tracks[clip]
    if S2 is None:
        last = new_tracks['Death'][1][-1]
        S2 = np.tile(last, (len(T), 1))
    an['channels'] = [c for c in an['channels'] if not (names[c['target']['node']].startswith('Skirt_') and c['target']['path'] == 'rotation')]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    doc['accessors'][tacc]['min'] = [float(T.min())]; doc['accessors'][tacc]['max'] = [float(T.max())]
    for k, nm in enumerate(RING):
        H = hinge[nm]
        node = doc['nodes'][H['i']]
        q0 = np.array(node.get('rotation', [0, 0, 0, 1]), float)
        Q = []
        for a in S2[:, k]:
            q_ax = rot_q(H['ax'], a)
            x1, y1, z1, w1 = q_ax; x2, y2, z2, w2 = q0
            q = np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
            Q.append(q / np.linalg.norm(q))
        Q = np.array(Q, np.float32)
        qa = g.append_accessor(Q, 'VEC4')
        an['samplers'].append(dict(input=tacc, output=qa, interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=H['i'], path='rotation')))
g.write(Path(OUT))
json.dump(rep, open(REP, 'w'), indent=1)
print('SKIRT keyed', OUT)
