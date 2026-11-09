#!/usr/bin/env python3
"""Hands by connectivity (humanoid playbook rule) on the separate hand pieces of work/step1_mesh.npz -> work/hands.json.
Geodesic distance over the hand piece from its wrist; the super-level sets {d > t} split into the five fingers as t
rises. A finger = the earliest component (lowest t) that contains exactly one fingertip leaf and never splits again;
its vertices are that component, its base the component's lowest ring. Chain points: base pulled 1.5 cm back into the
palm (knuckle), then the finger's own centroid path by d, resampled at 0.42 / 0.72 of its length and the tip.
Thumb = the finger whose base lies nearest the wrist; index..pinky ordered by distance from the thumb base.
Hand frame: Y = wrist -> middle knuckle, palm normal from the knuckle line and the hand axis (sign: toward the
fingertips' curl side, i.e. away from the back-of-hand bulge), X = Y x Z (flexion axis)."""
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work' / 'step1_mesh.npz'); co, pv, tri = d['co'], d['piece'], d['tri']
J = json.load(open(P / 'work' / 'joints.json'))['human']
NAMES = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
out = {}
for side, hp in (('L', 5), ('R', 6)):
    wr = np.array(J['Hand_' + side])
    ids = np.where(pv == hp)[0]; idx = -np.ones(len(co), int); idx[ids] = np.arange(len(ids))
    t = tri[(pv[tri] == hp).all(1)]
    E = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1), axis=0)
    a, b = idx[E[:, 0]], idx[E[:, 1]]; w = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
    G = coo_matrix((np.r_[w, w], (np.r_[a, b], np.r_[b, a])), shape=(len(ids),) * 2).tocsr()
    c = co[ids]
    seed = np.argsort(np.linalg.norm(c - wr, axis=1))[:6]
    dd = dijkstra(G, indices=seed, min_only=True)
    ths = np.arange(0.03, dd.max(), 0.005)
    comps = []
    for th in ths:
        m = np.where(dd > th)[0]
        nc, lab = connected_components(G[m][:, m], directed=False)
        comps.append([set(m[lab == k].tolist()) for k in range(nc) if (lab == k).sum() >= 2])
    kmax = max(range(len(comps)), key=lambda k: (len(comps[k]) >= 5, -k if len(comps[k]) >= 5 else 0))
    leaves = sorted(comps[kmax], key=len, reverse=True)[:5]
    fingers = []
    for leaf in leaves:
        best, bt = leaf, ths[kmax]
        for k in range(kmax - 1, -1, -1):
            holder = [cc for cc in comps[k] if leaf & cc]
            if not holder:
                break
            cc = holder[0]
            if sum(1 for other in leaves if other is not leaf and other & cc):
                break
            best, bt = cc, ths[k]
        v = np.array(sorted(best)); fingers.append((v, bt))
    # thumb: the base nearest the wrist (lowest separation threshold)
    fingers.sort(key=lambda f: f[1])
    thumb = fingers[0]
    base_of = lambda f: c[f[0][dd[f[0]] < f[1] + 0.012]].mean(0)
    rest = sorted(fingers[1:], key=lambda f: np.linalg.norm(base_of(f) - base_of(thumb)))
    order = [thumb] + rest
    res = {'wrist': wr.tolist(), 'fingers': {}}
    for name, (v, bt) in zip(NAMES, order):
        dv = dd[v]; pts = []
        for lo in np.arange(bt, dv.max() + 1e-6, 0.008):
            m = (dv >= lo) & (dv < lo + 0.012)
            if m.sum():
                pts.append(c[v[m]].mean(0))
        tipv = c[v[np.argsort(-dv)[:3]]].mean(0)
        pts = np.array(pts + [tipv])
        axis = pts[-1] - pts[0]; axis /= np.linalg.norm(axis)
        knuckle = pts[0] - axis * (0.015 if name != 'Thumb' else 0.01)
        pts = np.vstack([knuckle, pts])
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        q = [np.array([np.interp(f * arc[-1], arc, pts[:, i]) for i in range(3)]) for f in (0, 0.42, 0.72, 1.0)]
        res['fingers'][name] = {'joints': [x.round(5).tolist() for x in q], 'verts': ids[v].tolist(),
                                'sep_threshold': round(float(bt), 3), 'length': round(float(arc[-1]), 4)}
        print(side, name, 'verts', len(v), 'sep', round(float(bt), 3), 'len', round(float(arc[-1]), 3), 'base', np.round(q[0], 3), 'tip', np.round(q[-1], 3))
    kn = {n: np.array(res['fingers'][n]['joints'][0]) for n in NAMES}
    Y = kn['Middle'] - wr; Y /= np.linalg.norm(Y)
    lat = kn['Index'] - kn['Pinky']; lat -= Y * (lat @ Y); lat /= np.linalg.norm(lat)
    Z = np.cross(lat, Y)                                     # palm normal candidate
    # fingertips curl toward the palm: the tips lie on the palm side of the knuckle plane in a relaxed hand
    tips = np.array([res['fingers'][n]['joints'][-1] for n in NAMES[1:]]).mean(0)
    if (tips - np.mean(list(kn.values()), 0)) @ Z < 0:
        Z = -Z
    X = np.cross(Y, Z)
    res['frame'] = {'X': X.round(5).tolist(), 'Y': Y.round(5).tolist(), 'Z_palm': Z.round(5).tolist()}
    res['hand_end'] = kn['Middle'].round(5).tolist()
    res['palm_verts'] = [int(i) for i in ids if not any(int(i) in set(res['fingers'][n]['verts']) for n in NAMES)]
    res['geo'] = {int(i): round(float(x), 4) for i, x in zip(ids, dd)}
    print(side, 'palm normal', np.round(Z, 3), 'hand axis', np.round(Y, 3))
    out[side] = res
(P / 'work' / 'hands.json').write_text(json.dumps(out))
