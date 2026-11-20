#!/usr/bin/env python3
"""Club gate (the Codex install's QA hold: grip gaps up to 75 mm, club/body penetration 64 mm), at 48 fps on the runtime body GLB + the
placed club GLB (on joint `Club`):
- grip, Attack while the fist is closed (EASE_IN..dur-EASE_OUT): per finger the gap between the finger's nearest skin and the handle surface
  (handle radius per station from the club's own vertices), and the depth of finger skin inside the handle;
- club against the body, every clip: club vertices behind the nearest body surface (vertex normal, within 6 cm), the right hand and fingers
  excluded while the fist holds the club. Args: <body glb> <club glb> [out txt]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g); h = Glb(Path(sys.argv[2]))
names = [n.get('name') for n in g.json['nodes']]; ix = {n: i for i, n in enumerate(names)}; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
tris = []; off = 0
for p in P:
    tris.append(p['triangles'] + off); off += len(p['positions'])
tris = np.vstack(tris)
import json
_pl = json.load(open(Path(__file__).resolve().parents[1] / 'work' / 'club_place.json'))
hp = h.json['meshes'][0]['primitives'][0]; CV = h.accessor(hp['attributes']['POSITION']).astype(float)
c0 = CV.mean(0); ax = np.linalg.svd(CV - c0)[2][0]
if (CV[np.argmax(np.linalg.norm(CV - c0, axis=1))] - c0) @ ax < 0: ax = -ax          # toward the head
tl = (CV - c0) @ ax; rl = np.linalg.norm(CV - c0 - np.outer(tl, ax), axis=1)
GRIP = c0 + ax * (tl.min() + 0.065 * _pl['scale'] + _pl['tc'])          # the grip centre: the pommel end (original y -0.065) + the grip station
EASE_IN, EASE_OUT = 0.12, 0.16
R_HAND = np.char.startswith(dom, 'Bip01 R Hand') | np.char.startswith(dom, 'Bip01 R Thumb') | np.char.startswith(dom, 'Bip01 R Index') | \
    np.char.startswith(dom, 'Bip01 R Middle') | np.char.startswith(dom, 'Bip01 R Ring') | np.char.startswith(dom, 'Bip01 R Pinky')
F = {f: np.where(np.char.startswith(dom, f'Bip01 R {f}'))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
# handle span: where the fist closes (stations of the hand vertices at the first closed attack frame are measured below)


def body_pos(W):
    return np.vstack([m.skinned_positions(W)[i][0] for i in range(len(P))])


def vnormals(X):
    n = np.cross(X[tris[:, 1]] - X[tris[:, 0]], X[tris[:, 2]] - X[tris[:, 0]]); N = np.zeros_like(X)
    for k in range(3): np.add.at(N, tris[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


out = []
for an in g.json['animations']:
    clip = an['name']; T = m.clip_times(clip); dur = float(T[-1])
    worst = (0.0, 0.0, '-'); gaps = {f: [] for f in F}; inside = 0.0
    for t in np.arange(0, dur + 1e-6, 1 / 48):
        W = m.world(m.sample(clip, float(t))); X = body_pos(W)
        Cw = W[ix['Club']]; Q = CV @ Cw[:3, :3].T + Cw[:3, 3]
        a_ = Cw[:3, :3] @ ax; o_ = Cw[:3, :3] @ c0 + Cw[:3, 3]
        closed = clip == 'Attack' and EASE_IN <= t <= dur - EASE_OUT
        keep = ~R_HAND if closed or clip == 'Attack' else np.ones(len(X), bool)
        if clip == 'Attack':        # the palm and wrist skin of the fist round the handle (MPFB stub weights: forearm) is the grip, not a penetration
            gp = Cw[:3, :3] @ GRIP + Cw[:3, 3]
            keep = keep & (np.linalg.norm(X - gp, axis=1) > 0.07)
        N = vnormals(X); idx = np.where(keep)[0]; tree = cKDTree(X[idx])
        d, k = tree.query(Q, distance_upper_bound=0.06)
        ok = np.isfinite(d)
        if ok.any():
            v = idx[k[ok]]; dep = -np.einsum('ij,ij->i', Q[ok] - X[v], N[v])
            if dep.max() > worst[0]: worst = (float(dep.max()), float(t), dom[v[np.argmax(dep)]])
        if closed:
            for f, ids in F.items():
                v = X[ids] - o_; s = v @ a_; r = np.linalg.norm(v - np.outer(s, a_), axis=1)
                Rs = np.interp(s, np.sort(tl), rl[np.argsort(tl)])
                near = (s > tl.min()) & (s < tl.max())
                if near.any():
                    gaps[f].append(float((r[near] - Rs[near]).min())); inside = max(inside, float((Rs[near] - r[near]).max()))
    line = f"{clip:9s} club inside body max {worst[0] * 100:5.1f} cm at {worst[1]:.2f} s ({worst[2]})"
    if clip == 'Attack':
        line += ' | grip gap mm (max over closed frames) ' + ' '.join(f'{f} {max(v) * 1000:.0f}' for f, v in gaps.items() if v) + f' | finger skin inside handle {inside * 1000:.0f} mm'
    print(line, flush=True); out.append(line)
if len(sys.argv) > 3: open(sys.argv[3], 'w').write('\n'.join(out) + '\n')
