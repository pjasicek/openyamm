#!/usr/bin/env python3
"""Where a hand enters the body: per clip and side, the contact episodes (hand/forearm vertices > 1 cm behind an outer
body face, the arm_hand_gate's exact test, every face not on that arm), with the frames, the deepest depth, the joint the
entered face belongs to and the depth-weighted mean face normal. Args: <glb> [clip,clip...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
m = Model(Glb(Path(sys.argv[1]))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist')
HAND = ('Hand', 'Forearm', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
def skin(w):
    sp = m.skinned_positions(w); return np.concatenate([sp[k][0] for k in USE])
rest = skin(m.world({}))
clips = sys.argv[2].split(',') if len(sys.argv) > 2 else m.clips
for s in ('L', 'R'):
    tok = f' {s} '
    av = np.array([tok in d and any(k in d for k in ARM) for d in dom]); hv = np.where(np.array([tok in d and any(k in d for k in HAND) for d in dom]))[0]
    bf = np.where(~av[tris].any(1))[0]; bf = bf[outer_faces(rest, tris, bf)]
    for clip in clips:
        dur = max(m.clip_times(clip)); ts = np.arange(0, dur + 1e-6, 1 / 48)
        rows = []
        for k, t in enumerate(ts):
            X = skin(m.world(m.sample(clip, float(t)))); T = X[tris[bf]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
            n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
            rp = np.repeat(pts, 40, 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
            d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
            f = near[r, best]; side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, best], n[f])
            dep = np.where((side < 0) & (d[r, best] <= 0.12), -side, 0.0)
            i = int(dep.argmax())
            if dep[i] > 0.01:
                hitj = dom[tris[bf[f[i]]][0]]
                rows.append((k, dep[i], dom[hv[i]], hitj, n[f[i]]))
        if not rows:
            continue
        # episodes: gaps over 3 frames split
        eps = [[rows[0]]]
        for r_ in rows[1:]:
            (eps[-1].append(r_) if r_[0] - eps[-1][-1][0] <= 3 else eps.append([r_]))
        for e in eps:
            w = np.array([x[1] for x in e]); nn = (np.array([x[4] for x in e]) * w[:, None]).sum(0); nn /= np.linalg.norm(nn)
            hits = {}
            for x in e: hits[x[3]] = hits.get(x[3], 0) + 1
            parts = {}
            for x in e: parts[x[2]] = parts.get(x[2], 0) + 1
            kk = max(e, key=lambda x: x[1])
            print(f'{clip:12s} {s} f48 {e[0][0]}-{e[-1][0]} ({len(e)}f) max {kk[1]*100:.1f}cm@{kk[0]} arm {sorted(parts.items(), key=lambda x:-x[1])[:2]} into {sorted(hits.items(), key=lambda x:-x[1])[:3]} n {np.round(nn,2)}', flush=True)
