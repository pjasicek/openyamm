#!/usr/bin/env python3
"""Doublet skirt follows the thighs (overnight gate: thighs must not pass through the skirt in Walking and Running). MM9's own six hinge bones (Bone06/14/18/02/10/22, children of the Pelvis) carry MM9's cloth motion: MM9's skirt hangs still
in Walking and the thighs pass through it. Here each hinge keeps MM9's rotation and adds the least swing about its own frame that keeps the legs MARGIN under the cloth (cloth is fixed in the hinge's frame, so closed form: atan of radial excess
over depth, measured in that frame). Translations: the hinge stays rigid on Bip01 Spine, which carries the belt, instead of MM9's own offsets for its nearer pivot. Curves: running maximum (HOLD s) and Gaussian (SIGMA s; one-shots twice), circular on loops, on the clip's own
keys, never per frame. Side sectors take a share of their neighbours so the ring rises as one. Args: <in glb> <out glb> <report json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT, REP = sys.argv[1:4]
MARGIN, HOLD, SIGMA, MAXDEG, SKIRT_LEN, SECTOR = 0.025, 0.085, 0.035, 68.0, 0.26, 0.75
LOOPS = ('Standing', 'Walking', 'Running', 'Sit', 'StaticDie')
# Kira: the Argument cutscene clips start (and most end) seated, as Sit: their swing must not ease from or to zero there
SEATED_START = ('Applause', 'Sc2_KIRA5', 'Sc2_Kira7', 'Sc2_Kira9b', 'Sc2_KIRA12', 'Sc2_KIRA14', 'Sc2_KIRA16b')
SEATED_END = ('Applause', 'Sc2_KIRA5', 'Sc2_Kira7', 'Sc2_Kira9b', 'Sc2_KIRA12', 'Sc2_KIRA14')
RING = ['Bone06', 'Bone14', 'Bone18', 'Bone02', 'Bone10', 'Bone22']
NB = {k: ((k + 1) % 6, (k + 5) % 6) for k in range(6)}
g = Glb(Path(IN)); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
par = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
jn = [names[j] for j in m.joints]
PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
w0 = m.world({})
rest = allpos(w0)
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
legb = [i for i, n in enumerate(jn) if ('Thigh' in n or 'Calf' in n)]
legv = np.where((np.isin(J, legb) * W).sum(1) > 0.5)[0]
sk = [i for i, n in enumerate(jn) if n.startswith('Bone')]
sv = np.where((np.isin(J, sk) * W).sum(1) > 0.01)[0]
print('leg verts', len(legv), 'skirt verts', len(sv))
SP = ix['Bip01 Spine']
hinge = {}
c0 = np.mean([w0[ix[n]][:3, 3] for n in RING], 0)
for n in RING:
    i = ix[n]; R0i = np.linalg.inv(w0[i])
    down = R0i[:3, :3] @ np.array([0, -1.0, 0])
    d = w0[i][:3, 3] - c0; d[1] = 0; d /= np.linalg.norm(d)
    wd = d.copy()
    if n in ('Bone06', 'Bone02'): d = np.array([0, 0, np.sign(d[2])])
    nn = R0i[:3, :3] @ d
    ax = np.cross(down, nn); ax /= np.linalg.norm(ax)      # +angle swings the hanging cloth toward n
    H = dict(i=i, down=down, n=nn, ax=ax, sec=R0i[:3, :3] @ wd, spine_p=(np.linalg.inv(w0[SP]) @ w0[i])[:3, 3])
    restL = (R0i @ np.c_[rest[sv], np.ones(len(sv))].T).T[:, :3]
    cL = (R0i @ np.r_[c0, 1])[:3]
    dep = restL @ down; rad = restL @ nn
    sc = (restL - cL) - np.outer((restL - cL) @ down, down); sn = np.linalg.norm(sc, axis=1)
    ok = (sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR)
    bins = np.linspace(0.0, SKIRT_LEN, 9); surf = np.full(8, np.nan)
    for b in range(8):
        m_ = ok & (dep >= bins[b]) & (dep < bins[b + 1])
        if m_.any(): surf[b] = rad[m_].max()
    idx = np.where(~np.isnan(surf))[0]
    H['surf'] = (0.5 * (bins[:-1] + bins[1:]), np.interp(np.arange(8), idx, surf[idx]))
    hinge[n] = H


def rot_q(ax, a):
    s = np.sin(a / 2)
    return np.array([ax[0] * s, ax[1] * s, ax[2] * s, np.cos(a / 2)])


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def needs(x, w):
    """x: leg points (world); w: world matrices with each hinge rigid on the Spine and rotated by the clip; returns the swing per hinge (radians)."""
    out = np.zeros(6)
    cw = np.mean([w[hinge[n]['i']][:3, 3] for n in RING], 0)
    for k, nm in enumerate(RING):
        H = hinge[nm]; Li = np.linalg.inv(w[H['i']])
        y = (Li @ np.c_[x, np.ones(len(x))].T).T[:, :3]; c = (Li @ np.r_[cw, 1])[:3]
        depth = y @ H['down']; rad = y @ H['n']
        sc = (y - c) - np.outer((y - c) @ H['down'], H['down']); sn = np.linalg.norm(sc, axis=1)
        ok = (sn > 1e-6) & (depth > 0.01) & ((sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR)) & (np.hypot(depth, rad) < SKIRT_LEN + 0.03)
        if ok.any():
            R = np.interp(depth[ok], H['surf'][0], H['surf'][1])
            a = np.arctan2(rad[ok] + MARGIN, depth[ok]) - np.arctan2(R, depth[ok])
            out[k] = max(0.0, float(a.max()))
    return out


def rebuilt(w):
    """world matrices with the hinges rigid on the Spine at rest offset (rotation as the clip's)"""
    w = dict(enumerate(w)) if not isinstance(w, dict) else w
    return w


A0 = None
base = {}
def sample(clip, t):
    wl = m.world(m.sample(clip, float(t)))
    wl = np.array(wl, float)
    for nm in RING:
        H = hinge[nm]
        wl[H['i'], :3, 3] = (wl[SP] @ np.r_[H['spine_p'], 1])[:3]
    return wl
A0 = needs(rest[legv], np.array(w0, float))
print('rest need deg', np.round(np.degrees(A0), 1))
rep = {}
new_tracks = {}
for an in doc['animations']:
    clip = an['name']
    if clip == 'Dead': continue
    T = np.array(sorted(m.clip_times(clip))); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1); loop = clip in LOOPS
    A = np.zeros((n, 6))
    for f, t in enumerate(T):
        w = sample(clip, t)
        x = allpos(m.world(m.sample(clip, float(t))))[legv]
        A[f] = np.maximum(needs(x, w) - 0.45 * A0, 0)
    A = np.clip(A, 0, np.radians(MAXDEG))
    mode = 'wrap' if loop else 'nearest'
    sz = max(1, int(round(2 * HOLD / dt)) | 1)
    S = np.stack([gaussian_filter1d(maximum_filter1d(A[:, k], sz, mode=mode), (SIGMA if loop else (1.3 if clip == 'Death' else 2) * SIGMA) / dt, mode=mode) for k in range(6)], 1)
    S2 = S.copy()
    for k, (a, b) in NB.items():
        S2[:, k] = np.maximum(S[:, k], 0.55 * np.maximum(S[:, a], S[:, b]))
    if not loop:
        e = np.clip(T / 0.15, 0, 1); e = e * e * (3 - 2 * e)
        if clip != 'CowerEnd' and clip not in SEATED_START:          # the cower phases (script clips, 2026-10-31): CowerEnd starts crouched, CowerStart ends crouched
            S2 = S2 * e[:, None]
        if clip not in ('Death', 'Death2', 'CowerStart') and clip not in SEATED_END:
            e2 = np.clip((T[-1] - T) / 0.2, 0, 1); e2 = e2 * e2 * (3 - 2 * e2); S2 = S2 * e2[:, None]
    new_tracks[clip] = (T, S2)
    rep[clip] = {RING[k]: round(float(np.degrees(S2[:, k].max())), 1) for k in range(6)}
    print(clip, rep[clip], flush=True)
for an in doc['animations']:
    clip = an['name']
    if clip == 'Dead':
        T = np.array(sorted(m.clip_times('Dead'))); S2 = np.tile(new_tracks['Death'][1][-1], (len(T), 1))
    else:
        T, S2 = new_tracks[clip]
    Qs = {nm: [] for nm in RING}; Ts = {nm: [] for nm in RING}
    for f, t in enumerate(T):
        w = m.world(m.sample(clip, float(t)))
        for k, nm in enumerate(RING):
            H = hinge[nm]; i = H['i']; p = par[i]
            lw = np.linalg.inv(w[p]) @ w[i]                  # the clip's local rotation
            q = matrix_quaternion(lw[:3, :3]); q = qmul(q, rot_q(H['ax'], S2[f, k]))
            Qs[nm].append(q / np.linalg.norm(q))
            Ts[nm].append((np.linalg.inv(w[p]) @ w[SP] @ np.r_[H['spine_p'], 1])[:3])
    an['channels'] = [c for c in an['channels'] if not (names[c['target']['node']] in RING and c['target']['path'] in ('rotation', 'translation'))]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    doc['accessors'][tacc]['min'] = [float(T.min())]; doc['accessors'][tacc]['max'] = [float(T.max())]
    for nm in RING:
        Q = np.array(Qs[nm])
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] *= -1
        qa = g.append_accessor(Q.astype(np.float32), 'VEC4'); ta = g.append_accessor(np.array(Ts[nm], np.float32), 'VEC3')
        an['samplers'].append(dict(input=tacc, output=qa, interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=ix[nm], path='rotation')))
        an['samplers'].append(dict(input=tacc, output=ta, interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=ix[nm], path='translation')))
g.write(Path(OUT))
json.dump(rep, open(REP, 'w'), indent=1)
print('SKIRT keyed', OUT)
