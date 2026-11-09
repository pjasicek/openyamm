"""PeasantM5 full head of hair on Markel's head (positions only; UVs, weights, attributes, topology unchanged).
Markel's hair shell was sunk 1.5-3 mm under the face shell over his bald crown (crown_shrink.py). PeasantM5 has a full
head of hair, so every hair-shell vertex is set to a height H above the face shell (along the face normal at its
nearest point): H = TARGET inside, the shell's open boundary (front hairline, around the ears, nape) keeps its own
height (front hairline capped at EDGE so it does not stand as a step), Laplacian-diffused over the shell; vertices
already higher than H stay where they are.
Args: -- <in blend> <out blend> <face part> <hair part> [target 0.009] [edge 0.002] [report json]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, FACE, HAIR = a[0], a[1], int(a[2]), int(a[3])
TARGET = float(a[4]) if len(a) > 4 else 0.009
EDGE = float(a[5]) if len(a) > 5 else 0.002
REP = a[6] if len(a) > 6 else None
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
fv = [f for f in bm.faces if comp[f.verts[0].index] == FACE]
t = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in fv])
hv = [v for v in bm.verts if comp[v.index] == HAIR]
loc, nrm, d = {}, {}, {}
for v in hv:
    l, n, _, _ = t.find_nearest(v.co)
    loc[v.index], nrm[v.index], d[v.index] = l, n, (v.co - l).dot(n)
ZTOP = float(__import__('os').environ.get('ZTOP', '9.0'))
slit = {v.index for v in hv if any(e.is_boundary for e in v.link_edges) and v.co.z > ZTOP}
boundary = {v.index for v in hv if any(e.is_boundary for e in v.link_edges)} - slit
print('SLIT', len(slit), sorted(tuple(round(x, 3) for x in bm.verts[i].co) for i in slit))
fc = np.array([v.co[:] for v in bm.verts if comp[v.index] == FACE]).mean(0)
H = {}
for v in hv:
    if v.index in boundary:
        front = (v.co.y - fc[1]) < -0.02 and v.co.z > fc[2] + 0.04
        H[v.index] = EDGE if front and d[v.index] < EDGE else d[v.index]
    else:
        H[v.index] = max(d[v.index], TARGET)
# only the low (sunk) crown moves: every vertex already at or above TARGET is pinned at its own height
fixed = boundary | {v.index for v in hv if d[v.index] >= TARGET}
for i in fixed:
    if i not in boundary: H[i] = d[i]
ids = [v.index for v in hv]
nb = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in hv}
for _ in range(int(__import__('os').environ.get('ITERS', '15'))):
    nh = dict(H)
    for i in ids:
        if i in fixed: continue
        nh[i] = 0.5 * H[i] + 0.5 * np.mean([H[j] for j in nb[i]])
    H = nh
moved = 0; mx = 0.0
for v in hv:
    h = H[v.index] if v.index in boundary else max(H[v.index], d[v.index])
    delta = h - d[v.index]
    if abs(delta) > 1e-5:
        v.co = v.co + nrm[v.index] * delta; moved += 1; mx = max(mx, abs(delta))
# crown fairing: the face shell's own dents (a 5 mm pit at the crown) were copied by the offset; Laplacian-smooth the
# moved hair vertices (boundary fixed), positions only
movedset = [v for v in hv if v.index not in boundary and abs(max(H[v.index], d[v.index]) - d[v.index]) > 1e-5]
for _ in range(int(__import__('os').environ.get('FAIR', '6'))):
    newp = {}
    for v in movedset:
        nbv = [e.other_vert(v) for e in v.link_edges]
        c = sum((u.co for u in nbv), v.co * 0) / len(nbv)
        newp[v.index] = v.co + 0.5 * (c - v.co)
    for v in movedset:
        v.co = newp[v.index]
# poke check: face-shell vertices standing outside the moved hair shell (hair faces only)
bm.verts.ensure_lookup_table()
hf = [f for f in bm.faces if comp[f.verts[0].index] == HAIR]
th = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in hf])
poke = []
for v in bm.verts:
    if comp[v.index] != FACE: continue
    # poking: casting INWARD along the face normal meets the hair shell within 1.5 cm (hair below the skin)
    l, n, _, dist = th.ray_cast(v.co - v.normal * 0.0002, -v.normal, 0.015)
    if l is not None:
        poke.append((dist * 1000, v.index, tuple(round(x, 3) for x in v.co)))
poke.sort(reverse=True)
print('POKE', len(poke), poke[:6]); print('POKEHI', [p for p in poke if p[2][2] > 0.83])
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
r = dict(poke_face_vertices=len(poke), hair_vertices=len(hv), boundary=len(boundary), moved=moved, max_move_mm=mx * 1000, target_mm=TARGET * 1000, edge_mm=EDGE * 1000)
print('HAIR', r)
if REP: json.dump(r, open(REP, 'w'), indent=1)
