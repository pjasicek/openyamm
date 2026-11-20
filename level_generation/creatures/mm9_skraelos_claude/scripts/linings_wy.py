#!/usr/bin/env python3
"""Linings behind the open rims of one-sided cloth (see-through gate r1: the hood interior beside the jaw showed the background, 177 px in
Standing; the cowl's inner edge round the neck in the fall, 272 px). After PeasantDM2's rim_lining.py, for this project's npz meshes.
For every open boundary loop of the listed parts (edges with one face whose two positions are not shared with another part), the band of
that part's faces within DEPTH of the loop is duplicated OFFSET behind itself (along the vertex normal), flipped; the twins keep their
faces' UVs, part and `orig` (so the weights follow), and each loop edge is joined to its twin by a rim strip. Geometry is added only:
existing faces, UVs and weights are unchanged, so the paid paints stay valid.
r2: the band is the faces seen from behind at rest (visible_backfaces.py, HITS) grown by RINGS rings (the first version's 7 cm bands lined\n3,453 faces). Args: <asm npz> <mesh npz (with uv, orig)> <out mesh npz>"""
import sys, os
import numpy as np
from collections import defaultdict
A, U, OUT = sys.argv[1:4]; SPEC = [(x.split(':')[0], float(x.split(':')[1])) for x in sys.argv[4:]] or [('head', 0.07), ('mantle', 0.08)]
OFFSET = 0.002
S = np.load(A); co, tri, comp = S['co'], S['tri'], S['comp']; names = [str(x) for x in S['names']]
key = np.round(co, 5); _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True); inv = inv.ravel(); shared = cnt[inv] > 1
# vertex normals on the asm mesh (area-weighted, welded by position)
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
Nw = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Nw, inv[tri[:, c]], fn)
N = Nw[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
D = dict(np.load(U)); uco, utri, uvs, orig = D['co'], D['tri'], D['uv'], D['orig']
band_faces = set(); rim_edges = []          # asm faces (as sorted orig triples) and asm loop edges
# the band: faces seen from behind at rest (visible_backfaces.py) + RINGS rings of neighbours in the same part
HITS = os.environ.get('HITS', 'work/backfaces.npy'); RINGS = int(os.environ.get('RINGS', '2'))
hits = np.load(HITS)[:, 0].astype(int); posed_hits = np.zeros(0, int)
# r3: back faces seen in posed frames (posed_backfaces.py: rest centroids in the export GLB's frame, mirrored and lifted) mapped onto the
# frozen mesh's face centroids (axis flips and offsets from the two bounding boxes)
if os.environ.get('POSED', 'work/posed_backfaces.npy') and os.path.exists(os.environ.get('POSED', 'work/posed_backfaces.npy')):
    from scipy.spatial import cKDTree
    pc = np.load(os.environ.get('POSED', 'work/posed_backfaces.npy'))[:, :3]; fc_ = co[tri].mean(1)
    g = np.load(os.environ.get('GLBREST', 'work/glb_rest_bbox.npy'))      # [min xyz, max xyz] of the export's rest LOD0
    s_ = np.sign((g[1] - g[0]) * 0 + 1); amin, amax = co.min(0), co.max(0)
    flip = np.array([-1.0, 1.0, 1.0]); q = pc * flip
    qmin = np.minimum(g[0] * flip, g[1] * flip); off = amin - qmin; q = q + off
    d, nn = cKDTree(fc_).query(q); okp = d < 0.01
    posed_hits = np.unique(nn[okp]); print('POSED hits mapped', int(okp.sum()), 'of', len(pc), 'median d', round(float(np.median(d)), 4))
vf = defaultdict(list)
for f, t in enumerate(tri):
    for v in t: vf[inv[v]].append(f)
sel = set(int(f) for f in hits)
PR = {kv.split('=')[0]: int(kv.split('=')[1]) for kv in os.environ.get('PART_RINGS', 'head=2,hands=0').split(',') if kv}
for r_ in range(max([RINGS] + list(PR.values()))):
    grow = set()
    for f in sel:
        if r_ >= PR.get(names[comp[tri[f][0]]], RINGS): continue
        for v in tri[f]:
            grow.update(g for g in vf[inv[v]] if comp[tri[g][0]] == comp[tri[f][0]])
    sel |= grow
sel |= set(int(f) for f in posed_hits)          # posed hits: no rings (the rest hits' rings cover their neighbourhoods)
# open-loop bands (LOOPS 'part:zmax:depth'): the gown's open lower hem (z -0.40), seen from below in the fall (see-through r2: Death 124 px)
for spec in os.environ.get('LOOPS', '').split(','):
    if not spec: continue
    part, zmax, depth = spec.split(':'); k = names.index(part); zmax = float(zmax); depth = float(depth)
    fi = np.where(comp[tri[:, 0]] == k)[0]; ec = defaultdict(int)
    for f in fi:
        a_, b_, c_ = tri[f]
        for e in ((a_, b_), (b_, c_), (c_, a_)): ec[(min(e), max(e))] += 1
    lv = np.unique([v for e, m in ec.items() if m == 1 and not (shared[e[0]] and shared[e[1]]) for v in e]); lv = lv[co[lv, 2] < zmax]
    if len(lv):
        dd = np.min(np.linalg.norm(co[tri[fi]].mean(1)[:, None, :] - co[lv][None], axis=2), axis=1); add = fi[dd < depth]; sel |= set(int(f) for f in add)
        print('LOOP band', part, len(add), 'faces')
# Igrid: a box of a part's faces lined whole (BOXES 'part:x0,x1:y0,y1:z0,z1;...'): the hood round the face opening, whose inner side shows
# beside the neck from the front (see-through r2: collar 105 px in Running)
for spec in os.environ.get('BOXES', '').split(';'):
    if not spec: continue
    part, xr, yr, zr = spec.split(':'); k = names.index(part); (x0, x1), (y0, y1), (z0, z1) = [tuple(float(v) for v in r.split(',')) for r in (xr, yr, zr)]
    fc = co[tri].mean(1); bx = (comp[tri[:, 0]] == k) & (fc[:, 0] > x0) & (fc[:, 0] < x1) & (fc[:, 1] > y0) & (fc[:, 1] < y1) & (fc[:, 2] > z0) & (fc[:, 2] < z1)
    sel |= set(int(f) for f in np.where(bx)[0]); print('BOX band', part, int(bx.sum()), 'faces')
SKIP = [names.index(x) for x in os.environ.get('SKIP_PARTS', 'jewel').split(',') if x in names]      # the beads' open undersides lie on the choker
sel = set(f for f in sel if comp[tri[f][0]] not in SKIP)
for f in sel: band_faces.add(tuple(sorted(tri[f])))
for part in set(names[comp[tri[f][0]]] for f in sel):
    k = names.index(part); fi = np.where(comp[tri[:, 0]] == k)[0]; ec = defaultdict(list)
    for f in fi:
        a_, b_, c_ = tri[f]
        for e in ((a_, b_), (b_, c_), (c_, a_)): ec[(min(e), max(e))].append((f, e))
    be = [(e, fs[0]) for e, fs in ec.items() if len(fs) == 1 and not (shared[e[0]] and shared[e[1]]) and fs[0][0] in sel]
    for (e, (f, oe)) in be: rim_edges.append(oe)
    print('LINING', part, 'band faces', sum(1 for f in sel if comp[tri[f][0]] == k), 'rim edges', len(be))
# uv faces in the band (by their asm vertex triple)
utrip = [tuple(sorted(orig[t])) for t in utri]
pick = [i for i, t in enumerate(utrip) if t in band_faces]
newv = {}; P = list(uco); UV = list(uvs); O = list(orig); extra = {k: list(D[k]) for k in ('comp',) if k in D}
def twin(uvi):
    if uvi not in newv:
        newv[uvi] = len(P); o = orig[uvi]; P.append(uco[uvi] - N[o] * OFFSET); UV.append(uvs[uvi]); O.append(o)
        for k in extra: extra[k].append(D[k][uvi])
    return newv[uvi]
T = list(utri); MAT = list(D['mat']); INN = list(D['inner']) if 'inner' in D else [False] * len(utri)
for i in pick:
    a, b, c = utri[i]; T.append([twin(c), twin(b), twin(a)]); MAT.append(D['mat'][i]); INN.append(True)
# rim strips: for each loop edge, the uv face edge with the same asm vertices, joined to its twins
emap = {}
for i in pick:
    t = utri[i]
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): emap[(orig[a], orig[b])] = (a, b, i)
nr = 0
for a0, b0 in rim_edges:
    hit = emap.get((a0, b0))
    if hit is None: continue
    a, b, i = hit; at, bt = twin(a), twin(b)
    T += ([[b, a, at], [b, at, bt]] if os.environ.get('RIMFLIP') else [[a, b, bt], [a, bt, at]]); MAT += [D['mat'][i]] * 2; INN += [True, True]; nr += 1
D['co'] = np.array(P); D['uv'] = np.array(UV); D['orig'] = np.array(O); D['tri'] = np.array(T); D['mat'] = np.array(MAT); D['inner'] = np.array(INN)
for k in extra: D[k] = np.array(extra[k])
np.savez(OUT, **D); print('LINED', len(pick), 'twin faces,', nr, 'rim edges ->', OUT, len(T), 'faces')
