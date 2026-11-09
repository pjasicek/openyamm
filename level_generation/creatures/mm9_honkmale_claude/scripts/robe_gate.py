#!/usr/bin/env python3
"""Legs through the robe, per clip at 48 fps, on a runtime Honk GLB (LOD0). The Honk bodies have no thigh meshes: the legs are
two boot parts (Bip01 <S> Foot chains) reaching up inside the robe tube, so this is the boot's shaft and calf against the robe
wall. The test is true intersection: a boot edge crossing a triangle of the outer wall. A boot that leaves under the hem crosses
nothing; a boot through the cloth does. Point-on-side tests read the flared hem and the rim as "through", so they are not used.
The male's inner funnel is reported as `inner`: its edges through the outer wall, the only way it can be seen. Args: <glb> <out json> [clips, comma separated] [--hem-margin m]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from glb_pose import Glb, Model

glb, out = sys.argv[1:3]
want = sys.argv[3].split(',') if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
m = Model(Glb(glb))
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
idx = next(i for i, p in enumerate(m.primitives) if p['skinned'] and (p['positions'][:, 1].min() < 0.05))  # body material
pr = m.primitives[idx]
P, T = pr['positions'], pr['triangles']
_, inv = np.unique(np.round(P, 4), axis=0, return_inverse=True)
inv = inv.ravel()
e = np.r_[inv[T[:, [0, 1]]], inv[T[:, [1, 2]]], inv[T[:, [0, 2]]]]
n, cl = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(inv.max() + 1, inv.max() + 1)), directed=False)
part = cl[inv]
foot = {s: [names.index(f'Bip01 {s} {b}') for b in ('Foot', 'Toe0')] for s in 'LR'}
legs = {}
for s, ids in foot.items():
    w = np.where(np.isin(pr['joints'], ids), pr['weights'], 0).sum(1)
    c = np.bincount(part, w)
    legs[s] = int(c.argmax())
leg_mask = np.isin(part, list(legs.values()))
fp = part[T[:, 0]]
top = float(P[:, 1].max())
wallface = np.where(~np.isin(fp, list(legs.values())) & (P[T].mean(1)[:, 1] < 0.64 * top))[0]
# lining, rim and cap sit on one texel (zero UV area): cloth's other side, not a wall of its own
uv = g_uv = m.glb.accessor(doc['meshes'][doc['nodes'][pr['node']]['mesh']]['primitives'][idx]['attributes']['TEXCOORD_0'])
tu = uv[T[wallface]]
uv_area = np.abs((tu[:, 1, 0] - tu[:, 0, 0]) * (tu[:, 2, 1] - tu[:, 0, 1]) - (tu[:, 2, 0] - tu[:, 0, 0]) * (tu[:, 1, 1] - tu[:, 0, 1]))
wallface = wallface[uv_area > 1e-10]
# the outer wall: a rest face with nothing further out along its horizontal radius. What is left is the male's inner funnel, a
# shell nobody sees unless it comes out through the wall, which is reported as `inner`
A, B, C = P[T[wallface, 0]], P[T[wallface, 1]], P[T[wallface, 2]]
axis = np.array([np.median(P[np.unique(T[wallface]), 0]), 0, np.median(P[np.unique(T[wallface]), 2])])
cen = (A + B + C) / 3
rad = cen - axis
rad[:, 1] = 0
rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
e1, e2 = B - A, C - A
blocked = np.zeros(len(wallface), bool)
for f in range(len(wallface)):
    h = np.cross(rad[f], e2)
    det = (e1 * h).sum(1)
    o = cen[f] - A
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (o * h).sum(1) / det
        q_ = np.cross(o, e1)
        v = (q_ * rad[f]).sum(1) / det
        tt = (e2 * q_).sum(1) / det
    hit = (np.abs(det) > 1e-14) & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt > 0.01)
    blocked[f] = hit.any()
inner = wallface[blocked]
wallface = wallface[~blocked]
print('outer wall faces', len(wallface), 'inner shell faces', len(inner))
inner_v = np.unique(T[inner])
hem = float(P[np.unique(T[wallface])][:, 1].min())
print('wall faces', len(wallface), 'hem y', round(hem, 3), 'leg parts', legs, {s: (P[part == c, 1].min().round(3), P[part == c, 1].max().round(3)) for s, c in legs.items()})

def edges_of(mask):
    t = T[mask]
    e_ = np.sort(np.r_[t[:, [0, 1]], t[:, [1, 2]], t[:, [0, 2]]], axis=1)
    return np.unique(e_, axis=0)


def crossings(x, edges, faces):
    """Which edges cross which triangles (Moller-Trumbore, all pairs)."""
    o = x[edges[:, 0]][:, None]
    d = (x[edges[:, 1]] - x[edges[:, 0]])[:, None]
    A = x[T[faces, 0]][None]
    e1 = x[T[faces, 1]][None] - A
    e2 = x[T[faces, 2]][None] - A
    h = np.cross(d, e2)
    det = (e1 * h).sum(2)
    s_ = o - A
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (s_ * h).sum(2) / det
        q_ = np.cross(s_, e1)
        v = (d * q_).sum(2) / det
        tt = (e2 * q_).sum(2) / det
    shared = (T[faces][None, :, :] == edges[:, 0, None, None]).any(2) | (T[faces][None, :, :] == edges[:, 1, None, None]).any(2)
    return (np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (tt >= 0) & (tt <= 1) & ~shared, np.nan_to_num(tt)


CUT = float(next((a.split('=')[1] for a in sys.argv if a.startswith('--cut=')), 9))    # try a shorter boot shaft: rest heights
legL = edges_of(fp == legs['L'])
legR = edges_of(fp == legs['R'])
legL = legL[P[legL][:, :, 1].max(1) <= CUT]
legR = legR[P[legR][:, :, 1].max(1) <= CUT]
inn = edges_of(np.isin(np.arange(len(T)), inner)) if len(inner) else np.zeros((0, 2), int)
res = {}
for clip in [a['name'] for a in doc['animations']]:
    if want and clip not in want:
        continue
    dur = m.clip_times(clip)[-1]
    times = np.arange(0, dur + 1e-6, 1 / 48)
    per = {}
    for key, ed in (('L', legL), ('R', legR), ('inner', inn)):
        per[key] = dict(frames=0, worst=0, at=0, hmax=None)
    for ti, t in enumerate(times):
        x = m.skinned_positions(m.world(m.sample(clip, float(t))))[idx][0]
        for key, ed in (('L', legL), ('R', legR), ('inner', inn)):
            if not len(ed):
                continue
            hit, tt = crossings(x, ed, wallface)
            c = int(hit.any(1).sum())
            if c:
                per[key]['frames'] += 1
                if c > per[key]['worst']:
                    e_, f_ = np.nonzero(hit)
                    pts = x[ed[e_, 0]] + tt[e_, f_, None] * (x[ed[e_, 1]] - x[ed[e_, 0]])
                    per[key].update(worst=c, at=ti, hmax=round(float(pts[:, 1].max()), 3), rest_y=round(float(P[ed[e_]][:, :, 1].min()), 3))
    res[clip] = dict(of=len(times), **per)
    print(f'{clip:13s} /{len(times):3d} ' + '  '.join(f"{k}: {v['frames']:3d} frames, worst {v['worst']:2d} edges @f{v['at']} h{v['hmax']} rest_y>{v.get('rest_y')}" for k, v in per.items()), flush=True)
json.dump(res, open(out, 'w'), indent=1)
