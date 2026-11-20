"""Closedness and mirror partner of each loose part. Args: <blend>"""
import bpy, bmesh, sys, json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Meshy']; me = o.data
pa = next(a for a in me.attributes if a.data_type == 'INT' and a.name.startswith('part'))
part = np.zeros(len(me.vertices), int); pa.data.foreach_get('value', part)
v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
bm = bmesh.new(); bm.from_mesh(me)
open_e = {}; nm = {}
for e in bm.edges:
    c = part[e.verts[0].index]
    if e.is_boundary: open_e[c] = open_e.get(c, 0) + 1
    if not e.is_manifold and not e.is_boundary: nm[c] = nm.get(c, 0) + 1
tr = {}
for f in bm.faces:
    c = part[f.verts[0].index]; tr[c] = tr.get(c, 0) + 1
ids = sorted(tr)
cen = {c: v[part == c].mean(0) for c in ids}
ext = {c: v[part == c].max(0) - v[part == c].min(0) for c in ids}
for c in ids:
    m = cen[c] * [-1, 1, 1]
    pair = min((d for d in ids if d != c), key=lambda d: np.linalg.norm(cen[d] - m) + np.linalg.norm(ext[d] - ext[c]))
    err = np.linalg.norm(cen[pair] - m)
    # mirror distance: each vertex of c to nearest vertex of pair mirrored
    a = v[part == c]; b = v[part == pair] * [-1, 1, 1]
    d = np.sqrt(((a[:, None] - b[None]) ** 2).sum(-1)).min(1) if len(a) * len(b) < 4e6 else np.zeros(1)
    print(f'P{c} tris {tr[c]} open {open_e.get(c,0)} nonman {nm.get(c,0)} cen {np.round(cen[c],3)} ext {np.round(ext[c],3)} pair P{pair} cenerr {err:.3f} vdist p90 {np.percentile(d,90):.3f}')
