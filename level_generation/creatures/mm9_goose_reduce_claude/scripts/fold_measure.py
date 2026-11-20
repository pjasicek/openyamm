#!/usr/bin/env python3
"""Fold/stretch measure on a skinned GLB (2026-10-30 shoulder fold fix; the fold-over count is the reported number), every clip at 48 fps (LOD0).
Per triangle per frame:
  area   posed/bind area ratio
  flip   posed face normal vs LBS-predicted normal (mean blended 3x3 of its corners @ bind normal) dot < 0
  crease dihedral change between welded neighbours (degrees) vs bind
Region = the triangle's dominant bone. Usage: fold.py <glb> [json] [--frames clip:frame,...]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

path = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
m = Model(Glb(path))
doc = m.glb.json
names = [doc['nodes'][j].get('name') for j in m.joints]
prim = max(m.primitives, key=lambda p: len(p['triangles']))   # body
HELPERS = []
pi = m.primitives.index(prim)
for a in sys.argv:
    if a.startswith('--weights='):   # npz with W (blend vertex order) + bones + co (Blender world): trial weights
        from scipy.spatial import cKDTree
        dz = np.load(a.split('=', 1)[1])
        g = np.c_[dz['co'][:, 0], dz['co'][:, 2], -dz['co'][:, 1]]
        dist, vi = cKDTree(g).query(prim['positions'])
        assert dist.max() < 1e-4, dist.max()
        jn = {doc['nodes'][j]['name']: k for k, j in enumerate(m.joints)}
        HELPERS = [str(b) for b in dz['bones'] if str(b).startswith('H_')]
        for h in HELPERS:
            jn[h] = len(jn)
        Wb = dz['W'][vi]
        order = np.argsort(-Wb, 1)[:, :4]
        bn = [str(b) for b in dz['bones']]
        prim['joints'] = np.vectorize(lambda c: jn[bn[c]])(order)
        ww = np.take_along_axis(Wb, order, 1)
        prim['weights'] = ww / ww.sum(1, keepdims=True)
        if 'P' in dz.files:
            NP = dz['P'][vi]
            prim['positions'] = np.c_[NP[:, 0], NP[:, 2], -NP[:, 1]]
names = names + HELPERS
P0 = prim['positions']; T = prim['triangles']; J = prim['joints']; Wt = prim['weights']
# weld
key = np.round(P0, 5)
_, weld = np.unique(key, axis=0, return_inverse=True)
weld = weld.ravel()
TW = weld[T]
# triangle dominant bone
tw = np.zeros((len(T), len(m.joints) + len(HELPERS)))
for c in range(3):
    for k in range(4):
        np.add.at(tw, (np.arange(len(T)), J[T[:, c], k]), Wt[T[:, c], k])
dom = tw.argmax(1)
srt = np.sort(tw, 1)
mixed = srt[:, -2] / 3 > 0.2   # second bone >= 0.2 of the triangle
# edge adjacency (welded) for dihedral
E = {}
for f, t in enumerate(TW):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        E.setdefault((min(a, b), max(a, b)), []).append(f)
pairs = np.array([v for v in E.values() if len(v) == 2])
WE = np.array(list(E.keys()))


def fnorm(p):
    n = np.cross(p[T[:, 1]] - p[T[:, 0]], p[T[:, 2]] - p[T[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-15)[:, None], a


n0, a0 = fnorm(P0)
good = a0 > np.percentile(a0, 1) * 0.5
# body only: the largest welded component (teeth, claws and eyes are separate small pieces)
par = np.arange(weld.max() + 1)
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for t_ in TW:
    for a_, b_ in ((t_[0], t_[1]), (t_[1], t_[2])):
        ra, rb = find(a_), find(b_)
        if ra != rb: par[ra] = rb
root = np.array([find(x) for x in range(len(par))])
big = np.bincount(root).argmax()
good &= root[TW[:, 0]] == big
d0 = np.degrees(np.arccos(np.clip((n0[pairs[:, 0]] * n0[pairs[:, 1]]).sum(1), -1, 1)))

clips = [a['name'] for a in doc['animations']]
frames_only = None
for a in sys.argv:
    if a.startswith('--frames='):
        frames_only = a.split('=', 1)[1]
box = None
for a in sys.argv:
    if a.startswith('--box='):
        bx = [float(v) for v in a.split('=', 1)[1].split(',')]
        cen = P0[T].mean(1); cb = np.c_[cen[:, 0], -cen[:, 2], cen[:, 1]]
        box = (cb[:, 0] > bx[0]) & (cb[:, 0] < bx[1]) & (cb[:, 1] > bx[2]) & (cb[:, 1] < bx[3]) & (cb[:, 2] > bx[4]) & (cb[:, 2] < bx[5])
HALF = 0.5
for a in sys.argv:
    if a.startswith('--half='):
        HALF = float(a.split('=')[1])
dump = None
for a in sys.argv:
    if a.startswith('--dump='):
        c_, f_, o_ = a.split('=', 1)[1].split(',')
        dump = (c_, int(f_), o_)
rep = {'glb': path, 'tris': int(len(T)), 'clips': {}}
per_bone = {}
per_bone_over = {}
for clip in clips:
    ts = m.clip_times(clip)
    times = np.arange(ts[0], ts[-1] + 1e-6, 1 / 48)
    worst = []
    cflip = carea = ccrease = cover = sover = 0
    for fi, t in enumerate(times):
        world = m.world(m.sample(clip, t))
        pal = world[m.joints] @ m.inverse_binds
        if HELPERS:
            from glb_pose import trs_matrix, slerp
            loc = m.sample(clip, t)
            extra = []
            for h in HELPERS:
                node = next(i for i, nd in enumerate(doc['nodes']) if nd.get('name') == h[2:])
                tr, ro, scl = loc.get(node, m.rest[node])
                r0 = m.rest[node][1]
                # delta = r0^-1 * ro (xyzw quats)
                def qmul(a, b):
                    ax, ay, az, aw = a; bx, by, bz, bw = b
                    return np.array([aw*bx + ax*bw + ay*bz - az*by, aw*by - ax*bz + ay*bw + az*bx,
                                     aw*bz + ax*by - ay*bx + az*bw, aw*bw - ax*bx - ay*by - az*bz])
                inv0 = np.array([-r0[0], -r0[1], -r0[2], r0[3]])
                dlt = qmul(inv0, ro)
                half = slerp(np.array([0, 0, 0, 1.0]), dlt, HALF)
                local = trs_matrix(tr, qmul(r0, half), scl)
                wh = world[m.parent[node]] @ local
                k = m.joints.index(node)
                extra.append(wh @ m.inverse_binds[k])
            pal = np.concatenate([pal, np.array(extra)])
        bl = np.einsum('vk,vkij->vij', Wt, pal[J])
        P = np.einsum('vij,vj->vi', bl, np.concatenate([P0, np.ones((len(P0), 1))], 1))[:, :3]
        n, a = fnorm(P)
        R = bl[:, :3, :3][T].mean(1)
        pred = np.einsum('fij,fj->fi', R, n0)
        pred /= np.maximum(np.linalg.norm(pred, axis=1), 1e-12)[:, None]
        flip = ((n * pred).sum(1) < 0) & good
        ar = a / np.maximum(a0, 1e-15)
        d = np.degrees(np.arccos(np.clip((n[pairs[:, 0]] * n[pairs[:, 1]]).sum(1), -1, 1)))
        dd = d - d0
        crease_e = (dd > 70)
        crease_f = np.zeros(len(T), bool)
        crease_f[pairs[crease_e].ravel()] = True
        crease_f &= good
        squash = (ar < 0.15) & good
        # fold-over: face against its posed neighbourhood (welded) normal
        fo = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        vn = np.zeros((weld.max() + 1, 3))
        for c_ in range(3):
            np.add.at(vn, TW[:, c_], fo)
        for _ in range(4):
            acc = vn.copy(); np.add.at(acc, WE[:, 0], vn[WE[:, 1]]); np.add.at(acc, WE[:, 1], vn[WE[:, 0]])
            vn = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
        over = ((fo * vn[TW].mean(1)).sum(1) < 0) & good
        if box is not None:
            over &= box
        cover = max(cover, int(over.sum())); sover += int(over.sum())
        for b in np.unique(dom[over]):
            s_ = per_bone_over.setdefault(names[b], {})
            s_[clip] = s_.get(clip, 0) + int((over & (dom == b)).sum())
        bad = flip | crease_f | squash
        if box is not None:
            bad &= box
        cflip = max(cflip, int(flip.sum())); ccrease = max(ccrease, int(crease_e.sum())); carea = max(carea, int(squash.sum()))
        if bad.any():
            for b in np.unique(dom[bad]):
                nm = names[b]
                s = per_bone.setdefault(nm, {})
                s[clip] = s.get(clip, 0) + int((bad & (dom == b)).sum())
        if dump and dump[0] == clip and dump[1] == fi:
            vv = np.unique(T[over if '--dumpover' in sys.argv else bad].ravel())
            np.save(dump[2], np.c_[P0[vv, 0], -P0[vv, 2], P0[vv, 1]])
        worst.append((int(bad.sum()), fi, int(flip.sum()), int(crease_e.sum()), int(squash.sum()),
                      float(np.percentile(ar[good], 0.5)), float(np.percentile(ar[good], 99.5))))
    worst.sort(reverse=True)
    rep['clips'][clip] = {'max_over': cover, 'sum_over': sover, 'frames': len(times), 'max_bad': worst[0][0], 'max_flip': cflip, 'max_crease_edges': ccrease,
                          'max_squash': carea, 'sum_bad': int(sum(w[0] for w in worst)),
                          'worst_frames': [{'frame': w[1], 'bad': w[0], 'flip': w[2], 'crease': w[3], 'squash': w[4],
                                            'area_p0.5': round(w[5], 3), 'area_p99.5': round(w[6], 3)}
                                           for w in worst[:4]]}
    print(clip, 'over max/sum', cover, sover, json.dumps(rep['clips'][clip]['worst_frames'][:1]), 'sum_bad', rep['clips'][clip]['sum_bad'])
rep['per_bone'] = {k: v for k, v in sorted(per_bone.items(), key=lambda kv: -sum(kv[1].values()))}
for k, v in list(rep['per_bone'].items())[:12]:
    print(k, v)
GROUPS = {'shoulders': ['Bone11', 'Bone16', 'Bone12', 'Bone17', 'Bone32'], 'neck': ['Bone26', 'Bone35'],
          'head': ['Bone27', 'Bone28', 'Bone30', 'Bone37', 'Bone39'],
          'hips_tail': ['Bone33', 'Bone01', 'Bone06', 'Bone02', 'Bone07', 'Bone34', 'Bone21', 'Bone22', 'Bone23', 'Bone24'],
          'lower_legs': ['Bone13', 'Bone19', 'Bone18', 'Bone05', 'Bone03', 'Bone09', 'Bone08', 'Bone42']}
rep['groups'] = {g: sum(sum(per_bone.get(b, {}).values()) for b in bs) for g, bs in GROUPS.items()}
rep['groups_by_clip'] = {g: {c: sum(per_bone.get(b, {}).get(c, 0) for b in bs) for c in clips} for g, bs in GROUPS.items()}
print('GROUPS', rep['groups'])
rep['groups_over'] = {g: sum(sum(per_bone_over.get(b, {}).values()) for b in bs) for g, bs in GROUPS.items()}
rep['groups_over_by_clip'] = {g: {c: sum(per_bone_over.get(b, {}).get(c, 0) for b in bs) for c in clips} for g, bs in GROUPS.items()}
print('GROUPS_OVER', rep['groups_over'])
rep['total_over'] = sum(c['sum_over'] for c in rep['clips'].values())
print('OVER', rep['total_over'], {c: (v['max_over'], v['sum_over']) for c, v in rep['clips'].items()})
rep['total_bad'] = sum(c['sum_bad'] for c in rep['clips'].values())
print('TOTAL', rep['total_bad'])
if out:
    json.dump(rep, open(out, 'w'), indent=1)
