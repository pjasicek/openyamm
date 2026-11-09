#!/usr/bin/env python3
"""Part-through-part per clip at 48 fps (this body has no cloth geometry: the leather is paint; the same measure for what can pierce): tail vertices inside thigh/calf, thigh/calf inside the tail, upper teeth inside the jaw skin, lower teeth inside the head skin, jaw and head skin inside the torso, hands excluded (arm gate). Signed distance to the nearest triangle of the target with the outward normal; a point counts when behind the surface within REACH.
Args: <glb> <out json> [clips]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
m = Model(Glb(sys.argv[1])); doc = m.glb.json; jn = [doc['nodes'][j]['name'] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, off, dom, wJaw, wHead = [], 0, [], [], []
ij = jn.index('Box05'); ih = jn.index('Bip01 Head')
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
isd = lambda *k: np.array([any(x in d for x in k) for d in dom])
tail = isd('Box01', 'Box02', 'Box03', 'XhalfBox'); leg = isd('Thigh', 'Calf', 'Foot', 'Toe0')
jaw = dom == 'Box05'; head = dom == 'Bip01 Head'; torso = isd('Spine', 'Pelvis')
facesof = lambda mask: np.where(mask[tris].all(1))[0]
PAIRS = {'tail_in_leg': (tail, facesof(leg), .05), 'leg_in_tail': (leg, facesof(tail), .05), 'jaw_in_torso': (jaw, facesof(torso), .08), 'head_in_torso': (head, facesof(torso), .08), 'tail_in_torso': (tail & ~isd('Box01'), facesof(torso), .08)}
def pose(w):
    sp = m.skinned_positions(w); return np.concatenate([sp[k][0] for k in USE])
def depth(pts, X, faces, reach):
    T = X[tris[faces]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=min(16, len(faces)))
    rp = np.repeat(pts, near.shape[1], 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
    cp = q.reshape(*near.shape, 3)[r, best]; side = np.einsum('ij,ij->i', pts - cp, n[near[r, best]])
    return np.where((side < 0) & (d[r, best] <= reach), -side, 0)
bind = np.concatenate([np.asarray(P[k]['positions'], float) for k in USE])
for k, (src, faces, reach) in list(PAIRS.items()):
    # points that sit on the target in the bind are one surface with it (neck ring, tail root, hip): only the free ones count
    tgt = np.unique(tris[faces]); dd = cKDTree(bind[tgt]).query(bind[src])[0]; s2 = src.copy(); s2[np.where(src)[0][dd < .10]] = False; PAIRS[k] = (s2, faces, reach); print(k, 'free points', int(s2.sum()), flush=True)
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else [a['name'] for a in doc['animations']]
rep = {}
for c in clips:
    Te = m.clip_times(c)[-1]; ts = np.arange(0, Te + 1e-6, 1 / 48); rr = {k: [0, 0.] for k in PAIRS}
    for t in ts[::1 if c in ('Walking', 'Running') else 2]:
        X = pose(m.world(m.sample(c, float(t))))
        for k, (src, faces, reach) in PAIRS.items():
            d = depth(X[src], X, faces, reach).max()
            if d > .01: rr[k][0] += 1
            rr[k][1] = max(rr[k][1], float(d))
    rep[c] = {k: [v[0], round(v[1] * 100, 1)] for k, v in rr.items()}
    print(f'{c:13s} frames {len(ts):4d} ' + ' '.join(f'{k} {v[0]}f {round(v[1]*100,1)}cm' for k, v in rr.items()), flush=True)
json.dump(rep, open(sys.argv[2], 'w'), indent=1)
