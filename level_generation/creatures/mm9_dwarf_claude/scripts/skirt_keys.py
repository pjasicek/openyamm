#!/usr/bin/env python3
"""Tunic skirt follows the thighs (overnight gate: thighs must not pass through the skirt in Walking and Running). A closed ring on six hinge
bones `Skirt_*` at the belt, children of Bip01 Spine (the thighs' parent), weighted smoothly round the ring and by height (rig_guard.py).
Per key, in the Spine frame: pants points inside a hinge's sector and within the skirt's reach give the least swing about the hinge that keeps them
MARGIN under the cloth (closed form: atan of radial excess over depth). Curves: running maximum (HOLD s) and Gaussian (SIGMA s; one-shots twice), circular
on loops, on the clip's own keys, never per frame. Side sectors take a share of their neighbours so the ring rises as one. Body channels are not touched.
Run 2 (2026-10-31): the hem rides on the leg bones SkirtLeg* (skirt_leg_keys.py), so the hinges lift only the upper cloth: cap SK_MAXDEG 20 deg, no per-clip
margins (SK_CLIPM=1 restores them), and fix_pass() lifts, key by key, the hinge that clears a thigh the closed form missed (skirt_gate.py's test), up to MAXFIX.
Args: <in glb> <out glb> <report json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT, REP = sys.argv[1:4]
MARGIN, HOLD, SIGMA, MAXDEG, SKIRT_LEN, SECTOR = 0.035, 0.06, 0.03, float(__import__('os').environ.get('SK_MAXDEG', 20.0)), 0.27, 0.62
CLIP_MARGIN = {} if not __import__('os').environ.get('SK_CLIPM') else {'Running': 0.075, 'Walking': 0.065, 'Backpedal': 0.065, 'BackpedalRun': 0.065}
SHARE = 0.55
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
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
sk0 = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
legb = [i for i, n in enumerate(jn) if 'Thigh' in n or 'Calf' in n]
legw = np.isin(J, legb) * W
legv = np.where((legw.sum(1) > 0.5) & ((np.isin(J, sk0) * W).sum(1) < 0.001))[0]
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


def needs(y, S):
    """y: leg points, S: the skirt with its hinges at rest but following the thighs, both in the Spine frame; the swing each hinge still needs (radians)."""
    out = np.zeros(8)
    c = np.mean([hinge[x]['p'] for x in RING], 0)
    sc_ = (S - c) - np.outer((S - c) @ spine_up, spine_up); sn_ = np.linalg.norm(sc_, axis=1)
    yc = (y - c) - np.outer((y - c) @ spine_up, spine_up); yn = np.linalg.norm(yc, axis=1)
    for k, nm in enumerate(RING):
        H = hinge[nm]
        v = S - H['p']; dep = -(v @ spine_up); rad = v @ H['n']
        okS = (sc_ @ H['sec']) / np.maximum(sn_, 1e-6) > np.cos(SECTOR)
        if not okS.any(): continue
        bins = np.linspace(0.0, SKIRT_LEN, 9); surf = np.full(8, np.nan)
        for i in range(8):
            m_ = okS & (dep >= bins[i]) & (dep < bins[i + 1])
            if m_.any(): surf[i] = rad[m_].max()
        idx = np.where(~np.isnan(surf))[0]
        if not len(idx): continue
        R_ = np.interp(np.arange(8), idx, surf[idx]); hem = dep[okS].max()
        w_ = y - H['p']; depth = -(w_ @ spine_up); rr = w_ @ H['n']
        ok = (yn > 1e-6) & (depth > 0.01) & (depth < hem) & ((yc @ H['sec']) / np.maximum(yn, 1e-6) > np.cos(SECTOR))
        if ok.any():
            Rq = np.interp(depth[ok], 0.5 * (bins[:-1] + bins[1:]), R_)
            out[k] = max(0.0, float((np.arctan2(rr[ok] + MARGIN, depth[ok]) - np.arctan2(Rq, depth[ok])).max()))
    return out


# run 2: a second pass checks each key with the real skin (skirt_gate.py's test) and lifts the hinge whose cloth a thigh still pierces, STEP at a time
# up to MAXFIX: the closed form above reads the upper cloth near the hinge too shallow (Death2, AttackMelee2: the thigh's top swinging up under the belt)
import os
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from detached_parts_audit import closest_on_triangles
from scipy.spatial import cKDTree
STEP, MAXFIX, TOL = np.radians(4.0), np.radians(float(os.environ.get('MAXFIX', 50))), 0.003
gl = [i for i, n in enumerate(jn) if 'Thigh' in n]
glv = np.where(((np.isin(J, gl) * W).sum(1) > 0.5))[0]                      # skirt_gate.py's leg points
offs_ = np.cumsum([0] + [len(p['positions']) for p in PR]); tri_ = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs_)])
swv = (np.isin(J, sk0) * W).sum(1); face_ = np.where((swv[tri_] > 0.01).all(1))[0]
ft_ = rest[tri_[face_]]; n0_ = np.cross(ft_[:, 1] - ft_[:, 0], ft_[:, 2] - ft_[:, 0]); nn_ = n0_ / np.maximum(np.linalg.norm(n0_, axis=1, keepdims=True), 1e-12)
face_ = face_[((nn_ * (ft_.mean(1) * [1, 0, 1])).sum(1) > 0) & (np.abs(nn_[:, 1]) < 0.6)]
HW = np.zeros((len(rest), 8))                                                 # hinge share per vertex, ring order
for k, nm in enumerate(RING): HW[:, k] = (np.isin(J, [jn.index(nm)]) * W).sum(1)


def through_by_hinge(x):
    ft = x[tri_[face_]]; c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    q = x[glv]; _, near = cKDTree(c_).query(q, k=24); pts = np.repeat(q, 24, 0)
    qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
    dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
    fid = near[r, b]; v = q - qq.reshape(*near.shape, 3)[r, b]; s_ = np.einsum('ij,ij->i', v, n_[fid]); dist = dd[r, b]
    th = (s_ > 0.002) & (s_ > 0.98 * dist) & (dist < 0.2)
    out = np.zeros(8)
    for i in np.where(th)[0]:
        h = HW[tri_[face_[fid[i]]]].mean(0)
        if h.sum() > 0.05: out = np.maximum(out, s_[i] * h / h.max() * (h / h.max() > 0.4))
    return out, (float(s_[th].max()) if th.any() else 0.0)


def hinge_local(k, a):
    H = hinge[RING[k]]; q0 = np.array(doc['nodes'][H['i']].get('rotation', [0, 0, 0, 1]), float)
    x1, y1, z1, w1 = rot_q(H['ax'], a); x2, y2, z2, w2 = q0
    q = np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
    return q / np.linalg.norm(q)


def fix_pass(clip, T, S2, loop, dt):
    """greedy per key: of the hinges carrying the pierced cloth, lift the one that clears the most by STEP, while one still helps"""
    E = np.zeros_like(S2)
    def pose_through(f, loc, e):
        l2 = dict(loc)
        for k in range(8):
            i = hinge[RING[k]]['i']; tr = l2.get(i, [np.array(m.rest[i][0]), None, np.array(m.rest[i][2])])
            l2[i] = [np.array(tr[0]), hinge_local(k, min(S2[f, k] + e[k], MAXFIX)), np.array(tr[2])]
        return through_by_hinge(allpos(m.world(l2)))
    for f, t in enumerate(T):
        loc = m.sample(clip, float(t))
        per, top = pose_through(f, loc, E[f])
        for it in range(int(np.ceil(MAXFIX / STEP))):
            if top < TOL: break
            best = None
            for k in np.where(per > 0)[0]:
                if S2[f, k] + E[f, k] + STEP > MAXFIX: continue
                e = E[f].copy(); e[k] += STEP
                p2, t2 = pose_through(f, loc, e)
                if t2 < top - 0.0003 and (best is None or t2 < best[1]): best = (k, t2, p2)
            if best is None: break
            E[f, best[0]] += STEP; top, per = best[1], best[2]
    if not E.any(): return S2, 0.0
    mode = 'wrap' if loop else 'nearest'; sz = max(1, int(round(2 * HOLD / dt)) | 1)
    E = np.stack([gaussian_filter1d(maximum_filter1d(E[:, k], sz, mode=mode), (SIGMA if loop else 2 * SIGMA) / dt, mode=mode) for k in range(8)], 1)
    E2 = E.copy()
    for k, (a, b) in NB.items(): E2[:, k] = np.maximum(E[:, k], SHARE * np.maximum(E[:, a], E[:, b]))
    return np.minimum(S2 + E2, MAXFIX), float(np.degrees(E2.max()))


yr = (S0i @ np.c_[rest[legv], np.ones(len(legv))].T).T[:, :3]
A0 = needs(yr, (S0i @ np.c_[rest[sv], np.ones(len(sv))].T).T[:, :3])
print('rest need deg', np.round(np.degrees(A0), 1))
rep = {}
new_tracks = {}
for an in doc['animations']:
    clip = an['name']
    if clip == 'Dead': continue
    MARGIN = CLIP_MARGIN.get(clip, 0.035)
    T = np.array(sorted(m.clip_times(clip))); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1); loop = clip in LOOPS
    A = np.zeros((n, 8))
    for f, t in enumerate(T):
        w = m.world(m.sample(clip, float(t)))
        X_ = allpos(w); x = X_[legv]
        Si = np.linalg.inv(w[SP]); y = (Si @ np.c_[x, np.ones(len(x))].T).T[:, :3]; Ss = (Si @ np.c_[X_[sv], np.ones(len(sv))].T).T[:, :3]
        A[f] = np.maximum(needs(y, Ss) - A0, 0)
    A = np.clip(A, 0, np.radians(MAXDEG))
    mode = 'wrap' if loop else 'nearest'
    sz = max(1, int(round(2 * HOLD / dt)) | 1)
    S = np.stack([gaussian_filter1d(maximum_filter1d(A[:, k], sz, mode=mode), (SIGMA if loop else (1.3 if clip == 'Death' else 2) * SIGMA) / dt, mode=mode) for k in range(8)], 1)
    S2 = S.copy()
    for k, (a, b) in NB.items():
        S2[:, k] = np.maximum(S[:, k], SHARE * np.maximum(S[:, a], S[:, b]))
    if clip == 'Standing': BASE = S2.mean(0)                        # one-shots ease from and to Standing's own lift, not to nothing: Standing has the first key of every clip
    if not loop:
        e = np.clip(T / 0.15, 0, 1); e = e * e * (3 - 2 * e)
        S2 = BASE + (S2 - BASE) * e[:, None]
        if clip not in ('Death', 'Death2'):
            e2 = np.clip((T[-1] - T) / 0.2, 0, 1); e2 = e2 * e2 * (3 - 2 * e2); S2 = BASE + (S2 - BASE) * e2[:, None]
    S2, fixd = fix_pass(clip, T, S2, loop, dt)
    new_tracks[clip] = (T, S2)
    rep[clip] = {RING[k]: round(float(np.degrees(S2[:, k].max())), 1) for k in range(8)}
    print(clip, rep[clip], 'fix +%.1f deg' % fixd, flush=True)
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
