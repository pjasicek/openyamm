#!/usr/bin/env python3
"""Helmet rim against the torso (run 2). The old head gate (blade_gate.py with HEADMAT) counted every head-set vertex, so the neck tube that runs
into the collar by design read as 2.9 cm at rest. Here the head set is split by layer (work/head_faces.npz: Face 20, Helm 21, Eyes 22, Horns 23,
neck tube 24), matched to the GLB by UV. Per clip at 48 fps: the deepest helmet/horn point behind the torso's outer surface, and the same for the
face and beard (the beard lies on the chest, so only reported). Depth up to 8 cm by the nearest face normal (foot inside the face).
Args: <glb> <out json> [clips]"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
MAIN = __name__ == '__main__'
g = Glb(Path(sys.argv[1] if MAIN else os.environ['RIM_GLB'])); m = Model(g)
out = sys.argv[2] if MAIN else None
want = sys.argv[3].split(',') if MAIN and len(sys.argv) > 3 else None
doc = g.json; names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
prims = doc['meshes'][doc['nodes'][m.primitives[0]['node']]['mesh']]['primitives'][:len(P)]
mats = [doc['materials'][pr['material']]['name'] for pr in prims]
tri, off, dom, part = [], 0, [], []
Z = np.load(HERE / 'work' / 'head_faces.npz'); huv = Z['uv'].reshape(-1, 2); hpart = np.repeat(Z['part'], 3)
tree = cKDTree(huv)
for p, pr, mn in zip(P, prims, mats):
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
    if mn.startswith('DwarfHead'):
        uv = np.asarray(g.accessor(pr['attributes']['TEXCOORD_0']), float)
        d, i = tree.query(uv); pp = hpart[i]
        if np.percentile(d, 99) > 1e-3:       # the npz may hold the other v convention
            d2, i2 = tree.query(uv * [1, -1] + [0, 1]); pp = np.where(d2 < d, hpart[i2], pp); d = np.minimum(d, d2)
        print(mn, 'uv match p99', float(np.percentile(d, 99)))
        part.append(pp)
    else:
        part.append(np.zeros(len(p['positions']), int))
tri = np.concatenate(tri); dom = np.concatenate(dom); part = np.concatenate(part)
HAND = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm', 'UpperArm')
armv = np.array([any(k in d for k in HAND) or d in ('RHand1', 'LHand1') for d in dom])
headv = part > 0
X0 = np.concatenate([x for x, _ in [m.skinned_positions(m.world({}))[k] for k in range(len(P))]])
torso_f = np.where(~headv[tri].any(1) & ~armv[tri].any(1))[0]; torso_f = torso_f[outer_faces(X0, tri, torso_f)]
nc = X0[np.where(part == 24)[0]].mean(0)                 # the neck tube's centre: the torso's cap round it lies inside the tube and the helmet, unseen
cf = X0[tri[torso_f]].mean(1); torso_f = torso_f[np.hypot(cf[:, 0] - nc[0], cf[:, 2] - nc[2]) > float(os.environ.get('CAP_R', 0.10))]
T0 = X0[tri[torso_f]]; n0 = np.cross(T0[:, 1] - T0[:, 0], T0[:, 2] - T0[:, 0]); n0 /= np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
c0_ = T0.mean(1) - nc; rr_ = np.hypot(c0_[:, 0], c0_[:, 2]); inward = ((n0[:, 0] * c0_[:, 0] + n0[:, 2] * c0_[:, 2]) < -0.3 * rr_) & (rr_ < 0.17) & (c0_[:, 1] > -0.12)
torso_f = torso_f[(n0[:, 1] > -0.3) & ~inward]           # undersides facing down, and the collar's wall facing the neck tube (under the helmet): a helmet beyond them is not inside the body
helm = np.where(np.isin(part, (21, 23)))[0]; face = np.where(part == 20)[0]
print('helm/horn verts', len(helm), 'face/beard verts', len(face), 'torso faces', len(torso_f))


def depth(pts, X):
    T = X[tri[torso_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=24)
    rp = np.repeat(pts, near.shape[1], 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    dep = np.where((side < 0) & (d[rows, best] <= 0.08) & (np.abs(side) > 0.9 * d[rows, best]), -side, 0.0)
    depth.where = near[rows, best]
    return dep


if MAIN:
    res = {}
    for clip in m.clips:
        if want and clip not in want: continue
        dur = max(m.clip_times(clip)); hw = (0.0, 0); fw = 0.0; nb = 0
        for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
            X = np.concatenate([x for x, _ in m.skinned_positions(m.world(m.sample(clip, float(t))))[:len(P)]])
            dh = depth(X[helm], X); df = depth(X[face], X)
            if dh.max() > hw[0]:
                hw = (float(dh.max()), k); i_ = int(dh.argmax()); tf = torso_f[depth.where[i_]]
                hw_info = (X0[helm[i_]].round(3).tolist(), str(dom[tri[tf][0]]), X0[tri[tf]].mean(0).round(3).tolist())
            if os.environ.get('RIMDBG') and dh.max() > 0.01 and k % 6 == 0:
                m_ = dh > 0.01; print('   ', clip, k, 'n', int(m_.sum()), 'helm rest mean', X0[helm[m_]].mean(0).round(3), 'max', round(float(dh.max()) * 100, 1))
            fw = max(fw, float(df.max())); nb += int(dh.max() > 0.01)
        res[clip] = dict(helm_cm=round(hw[0] * 100, 1), frame48=hw[1], frames_over_1cm=nb, beard_cm=round(fw * 100, 1))
        if hw[0] > 0: res[clip]['where'] = hw_info
        print(f'{clip:13s} helmet/horns {hw[0] * 100:4.1f} cm (frame {hw[1]}, {nb} frames > 1 cm)  face/beard {fw * 100:4.1f} cm', res[clip].get('where', ''), flush=True)
    json.dump(res, open(out, 'w'), indent=1)
