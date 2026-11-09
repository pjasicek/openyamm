#!/usr/bin/env python3
"""Numeric checks for the eyes, teeth and mouth on a delivered GLB (LOD0 'Terror' primitive), every clip at 48 fps.

eyes     - each eyeball (separate shell, 60+ vertices, near-isotropic) against its socket (body vertices within 1.6
           eyeball radii of its centre): the socket's rigid motion (Kabsch) predicts where the eyeball belongs; the
           error is the largest eyeball-vertex distance from that prediction, also as a fraction of its radius.
teeth    - the same test for the root of every tooth (its fifth of vertices nearest the body) against the 24 nearest
           gum vertices, and for the tongue's root against the 60 nearest floor vertices; plus root_gap: how much
           farther the root gets from the gum surface (those vertices' triangles) than in the bind pose.
interior - texel stretch of the mouth interior: the largest singular value of the map from texture space to the posed
           surface, in units of the nominal texel size (1 = the texture shows at its nominal density, 2 = one texel
           covers twice its nominal length). After head_fix.py the set is the cavity's own atlas rectangle (nominal =
           its design density); for an older build pass --old-cavity <npz> (head_fix_cavity_v1.npz: the replaced
           Meshy cavity faces, nominal = their mean bind density).
lips     - head-front triangles around the mouth outside the cavity: posed / bind stretch (how far the lips and the
           mouth corners tear relative to the rest pose); bind values below the set's 5th percentile are clamped.
Since the texture pass (2026-10-30) the socket and gum sets are taken over welded positions, so a different UV seam
layout (which splits other vertices in the GLB) measures the same surface; --texpass finds the cavity through
work/uv_v3_bag.npz instead of the old atlas rectangle, nominal density scaled with the island.
Usage: seat_check.py <glb> [report.json] [--old-cavity work/head_fix_cavity_v1.npz] [--texpass]
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

TEX = 2048
args = sys.argv[1:]
old_cav = None
if '--old-cavity' in args:
    k = args.index('--old-cavity')
    old_cav = args[k + 1]
    del args[k:k + 2]
texpass = '--texpass' in args
if texpass:
    args.remove('--texpass')
glb_path = args[0]
out_path = args[1] if len(args) > 1 else None
HERE = Path(__file__).resolve().parents[1]
cav = None
if old_cav is None and (HERE / 'work' / 'head_fix.json').exists():
    cav = json.load(open(HERE / 'work' / 'head_fix.json'))['cavity']

glb = Glb(glb_path)
m = Model(glb)
prim = m.primitives[0]
uv = next(glb.accessor(me['primitives'][0]['attributes']['TEXCOORD_0']) for me in glb.json['meshes']
          if me['name'] == 'Terror').astype(np.float64)
P0 = m.skinned_positions(m.world({}))[0][0]
T = prim['triangles']
key = np.round(P0, 5)
_, weld = np.unique(key, axis=0, return_inverse=True)
weld = weld.ravel()
parent = np.arange(weld.max() + 1)


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for t in weld[T]:
    for a, b in ((t[0], t[1]), (t[1], t[2])):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
shell = np.array([find(w) for w in weld])
ids, counts = np.unique(shell, return_counts=True)
main = ids[counts.argmax()]
body_v = np.nonzero(shell == main)[0]
body_v = body_v[np.unique(weld[body_v], return_index=True)[1]]      # one vertex per position: seams change with the UVs
eyes, teeth, tongue = [], [], None
for s in ids:
    if s == main:
        continue
    v = np.nonzero(shell == s)[0]
    ext = np.ptp(P0[v], 0)
    if len(np.unique(weld[v])) >= 60 and ext.max() / max(ext.min(), 1e-6) < 1.3:
        eyes.append(v)
    elif ext.max() > 0.4:
        tongue = v
    else:
        teeth.append(v)


def point_tri_dist(p, A, B, C):
    """Distances from points p (n,3) to triangles (m,3 each): (n, m), by projection with edge clamping."""
    ab, ac = B - A, C - A
    n = np.cross(ab, ac)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    out = np.full((len(p), len(A)), np.inf)
    for i, q in enumerate(p):
        d = q - A
        h = (d * n).sum(1)
        x = q - h[:, None] * n
        # barycentric of the projection
        v2 = x - A
        d00, d01, d11 = (ab * ab).sum(1), (ab * ac).sum(1), (ac * ac).sum(1)
        d20, d21 = (v2 * ab).sum(1), (v2 * ac).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-18
        v = (d11 * d20 - d01 * d21) / den
        w = (d00 * d21 - d01 * d20) / den
        inside = (v >= 0) & (w >= 0) & (v + w <= 1)
        dist = np.where(inside, np.abs(h), np.inf)
        for P1, P2 in ((A, B), (B, C), (C, A)):
            e = P2 - P1
            t = np.clip(((q - P1) * e).sum(1) / ((e * e).sum(1) + 1e-18), 0, 1)
            dist = np.minimum(dist, np.linalg.norm(q - (P1 + t[:, None] * e), axis=1))
        out[i] = dist
    return out


def socket_of(v, radius_fn):
    c = P0[v].mean(0)
    r = float(np.linalg.norm(P0[v] - c, axis=1).mean())
    return c, r, body_v[np.linalg.norm(P0[body_v] - c, axis=1) < radius_fn(r)]


checks = []
for v in eyes:
    c, r, sock = socket_of(v, lambda r: 1.6 * r)
    checks.append({'kind': 'eye', 'v': v, 'c': c, 'r': r, 'sock': sock})
for v in teeth + ([tongue] if tongue is not None else []):
    d = np.array([np.min(np.linalg.norm(P0[body_v] - p, axis=1)) for p in P0[v]])
    rv = v[np.argsort(d)[:max(3, len(v) // 5)]]           # the embedded root
    root = P0[rv].mean(0)
    near = body_v[np.argsort(np.linalg.norm(P0[body_v] - root, axis=1))[:24 if v is not tongue else 60]]
    gum = np.nonzero(np.isin(T, near).any(1) & np.isin(T[:, 0], body_v))[0]
    checks.append({'kind': 'tongue' if v is tongue else 'tooth', 'v': rv, 'c': root,
                   'r': float(np.ptp(P0[v], 0).max()), 'sock': near, 'gum': gum,
                   'gap0': point_tri_dist(P0[rv], *(P0[T[gum, k]] for k in range(3))).min(1).mean()})


def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0)
    H = (a - ca).T @ (b - cb)
    U, _, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return R, cb - R @ ca


# ---- triangle sets
cen = P0[T].mean(1)
tuv = uv[T].mean(1)
sets = {}
if cav is not None and texpass:
    from scipy.spatial import cKDTree
    bag = np.load(HERE / 'work' / 'uv_v3_bag.npz')
    centre = bag['uv_new'].mean(1) * [1, -1] + [0, 1]            # glTF v
    d, near = cKDTree(centre).query(tuv)
    hit = d < 2e-4
    ratio = np.sqrt(np.abs(np.cross(*np.moveaxis(bag['uv_new'][bag['kind'] == 1][:, 1:] - bag['uv_new'][bag['kind'] == 1][:, :1], 1, 0))).sum()
                    / np.abs(np.cross(*np.moveaxis(bag['uv_old'][bag['kind'] == 1][:, 1:] - bag['uv_old'][bag['kind'] == 1][:, :1], 1, 0))).sum())
    sets['interior'] = (np.nonzero(hit & (bag['kind'][near] == 1))[0], cav['texels_per_metre'] * float(ratio))
    in_cav = hit.copy()
elif cav is not None:
    u0, v0, u1, v1 = cav['uv_rect_gltf']
    sets['interior'] = (np.nonzero((tuv[:, 0] >= u0) & (tuv[:, 0] <= u1) & (tuv[:, 1] >= v0) & (tuv[:, 1] <= v1))[0],
                        cav['texels_per_metre'])
    in_cav = np.zeros(len(T), bool)
    in_cav[sets['interior'][0]] = True
    c0, c1, c2, c3 = cav['cap_rect']          # the throat cap: a uniform dark swatch, in neither set
    in_cav |= (tuv[:, 0] >= c0) & (tuv[:, 0] <= c2) & (1 - tuv[:, 1] >= c1) & (1 - tuv[:, 1] <= c3)
elif old_cav is not None:
    oc = np.load(old_cav)['centroids_gltf']
    dmin = np.array([np.min(np.linalg.norm(oc - c, axis=1)) for c in cen])
    sel = np.nonzero(dmin < 1e-4)[0]
    sets['interior'] = (sel, None)
    in_cav = np.zeros(len(T), bool)
    in_cav[sel] = True
else:
    in_cav = np.zeros(len(T), bool)
# glTF: +Y up, the creature faces +Z; the mouth region in front of the head
lips = np.nonzero((np.abs(cen[:, 0] + 0.06) < 0.45) & (cen[:, 1] > 1.55) & (cen[:, 1] < 2.6) & (cen[:, 2] > 0.2)
                  & ~in_cav & np.isin(T[:, 0], body_v))[0]


def tex_map(ids):
    t = T[ids]
    D = np.stack([uv[t[:, 1]] - uv[t[:, 0]], uv[t[:, 2]] - uv[t[:, 0]]], 2)
    ok = np.abs(np.linalg.det(D)) > 1e-12
    return ids[ok], np.linalg.inv(D[ok])


def sv(P, ids, Dinv):
    t = T[ids]
    a = P[t[:, 0]]
    E = np.stack([P[t[:, 1]] - a, P[t[:, 2]] - a], 2)
    return np.linalg.svd(np.einsum('tij,tjk->tik', E, Dinv), compute_uv=False)[:, 0]


prep = {}
for k, (ids, dens) in sets.items():
    ids, Dinv = tex_map(ids)
    t = T[ids]
    if dens is None:
        a3 = 0.5 * np.linalg.norm(np.cross(P0[t[:, 1]] - P0[t[:, 0]], P0[t[:, 2]] - P0[t[:, 0]]), axis=1)
        au = 0.5 * np.abs(np.cross(np.c_[uv[t[:, 1]] - uv[t[:, 0]], np.zeros(len(t))],
                                   np.c_[uv[t[:, 2]] - uv[t[:, 0]], np.zeros(len(t))])[:, 2])
        dens = TEX * np.sqrt(au.sum() / a3.sum())
    prep[k] = (ids, Dinv, TEX / dens, None)
ids, Dinv = tex_map(lips)
bind = sv(P0, ids, Dinv)
prep['lips'] = (ids, Dinv, None, np.maximum(bind, np.percentile(bind, 5)))
report = {'glb': glb_path, 'eyes': [], 'teeth': [], 'stretch': {}, 'triangles': {k: int(len(v[0])) for k, v in prep.items()},
          'nominal_texels_per_m': {k: round(TEX / v[2], 1) for k, v in prep.items() if v[2]}}
worst = [dict(err=0.0, clip=None, frame48=0) for _ in checks]
stretch = {k: {} for k in prep}
for clip in m.clips:
    ts = np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 48)
    for fi, tt in enumerate(ts):
        P = m.skinned_positions(m.world(m.sample(clip, tt)))[0][0]
        for e, w in zip(checks, worst):
            R, tr = kabsch(P0[e['sock']], P[e['sock']])
            err = float(np.linalg.norm(P[e['v']] - (P0[e['v']] @ R.T + tr), axis=1).max())
            if err > w['err']:
                w.update(err=err, clip=clip, frame48=fi)
            if 'gum' in e:
                gap = point_tri_dist(P[e['v']], *(P[T[e['gum'], k]] for k in range(3))).min(1).mean() - e['gap0']
                if gap > w.get('gap', -1):
                    w.update(gap=gap, gap_clip=clip, gap_frame48=fi)
        for k, (ids, Dinv, nominal, bind) in prep.items():
            s = sv(P, ids, Dinv)
            s = s / nominal if bind is None else s / np.maximum(bind, 1e-9)
            cur = stretch[k].setdefault(clip, {'max': 0, 'p99': 0, 'frame48': 0})
            if s.max() > cur['max']:
                cur.update(max=round(float(s.max()), 2), p99=round(float(np.percentile(s, 99)), 2), frame48=fi)
for e, w in zip(checks, worst):
    row = {'centre_gltf': [round(float(x), 3) for x in e['c']], 'size': round(e['r'], 3),
           'socket_verts': int(len(e['sock'])), 'max_offset_m': round(w['err'], 4), 'clip': w['clip'],
           'frame48': w['frame48']}
    if e['kind'] == 'eye':
        row['max_offset_radius'] = round(w['err'] / e['r'], 3)
        report['eyes'].append(row)
    else:
        row['kind'] = e['kind']
        row['root_gap_increase_m'] = round(float(w['gap']), 4)
        row['root_gap_at'] = [w['gap_clip'], w['gap_frame48']]
        report['teeth'].append(row)
report['stretch'] = stretch
report['summary'] = {
    'eye_max_offset_m': max(r['max_offset_m'] for r in report['eyes']),
    'eye_max_offset_radius': max(r['max_offset_radius'] for r in report['eyes']),
    'tooth_max_offset_m': max([r['max_offset_m'] for r in report['teeth'] if r['kind'] == 'tooth'] or [0]),
    'tongue_max_offset_m': max([r['max_offset_m'] for r in report['teeth'] if r['kind'] == 'tongue'] or [0]),
    'tooth_root_gap_increase_m': max([r['root_gap_increase_m'] for r in report['teeth'] if r['kind'] == 'tooth'] or [0]),
    **{f'{k}_max': max(v['max'] for v in stretch[k].values()) for k in stretch},
    **{f'{k}_p99': max(v['p99'] for v in stretch[k].values()) for k in stretch}}
print(json.dumps(report['summary']))
if out_path:
    json.dump(report, open(out_path, 'w'), indent=1)
