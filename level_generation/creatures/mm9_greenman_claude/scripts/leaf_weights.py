"""Leaves ride the skin under them (mm9_greenman pass 2, orchestrator: 39 leaf parts > 1 cm off the body in Fidget2,
Running and Death). Every small loose part (at most MAXT triangles; not the hands, not the staff) takes, per vertex, the
weights of the nearest point on the carrier surfaces (the loose parts over CARRIER triangles: the body and head shells),
interpolated over that face's vertices by barycentric weight, normalised, at most 4 influences. Weights only.
Args: <in blend> <out blend> [MAXT 200] [CARRIER 500]"""
import bpy, bmesh, sys
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MAXT = int(a[2]) if len(a) > 2 else 200; CARRIER = int(a[3]) if len(a) > 3 else 500
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hn = bm.faces.layers.int['hand']
comp = {}; parts = []
for f0 in bm.faces:
    if f0 in comp: continue
    st = [f0]; comp[f0] = len(parts); P = [f0]
    while st:
        f = st.pop()
        for v in f.verts:
            for g in v.link_faces:
                if g not in comp: comp[g] = len(parts); st.append(g); P.append(g)
    parts.append(P)
gname = {g.index: g.name for g in body.vertex_groups}
BONES = {b.name for b in rig.data.bones}
def is_staff(P):
    v = P[0].verts[0]
    return any(gname.get(g.group) == 'Bone01' and g.weight > 0.5 for g in me.vertices[v.index].groups)
def tris(P): return sum(len(f.verts) - 2 for f in P)
carrier_faces = [f for P in parts if tris(P) > CARRIER and not P[0][hn] and not is_staff(P) for f in P]
targets = [P for P in parts if tris(P) <= MAXT and not P[0][hn] and not is_staff(P)]
cv = sorted({v for f in carrier_faces for v in f.verts}, key=lambda v: v.index); ci = {v: i for i, v in enumerate(cv)}
bvh = BVHTree.FromPolygons([v.co.copy() for v in cv], [[ci[v] for v in f.verts] for f in carrier_faces])
W = {}
def wts(vi):
    return {gname[g.group]: g.weight for g in me.vertices[vi].groups if gname.get(g.group) in BONES}
import os
RIGID = int(os.environ.get('RIGID_MAXT', '0'))   # pass 2b: parts up to this many triangles take ONE weight set, the skin's at their root
n = 0
for P in targets:
    vset = {v for f in P for v in f.verts}
    if tris(P) <= RIGID:
        root = min(vset, key=lambda v: bvh.find_nearest(v.co)[3])
        vset_eval = [root]
    else:
        vset_eval = vset
    for v in vset_eval:
        loc, nrm, fi, d = bvh.find_nearest(v.co)
        f = carrier_faces[fi]
        vs = list(f.verts)[:3] if len(f.verts) == 3 else list(f.verts)
        # barycentric on the (triangulated) face: use the triangle of the face containing loc best
        best = None
        for k in range(1, len(vs) - 1):
            t = (vs[0], vs[k], vs[k + 1])
            b = barycentric_transform(loc, t[0].co, t[1].co, t[2].co, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
            err = sum(max(0.0, -x) for x in b)
            if best is None or err < best[0]: best = (err, t, b)
        _, t, b = best
        acc = {}
        for vv, bb in zip(t, b):
            bb = max(0.0, bb)
            for k2, w in wts(vv.index).items():
                acc[k2] = acc.get(k2, 0.0) + bb * w
        top = sorted(acc.items(), key=lambda x: -x[1])[:4]
        s = sum(w for _, w in top)
        if s > 0:
            ws_ = {k2: w / s for k2, w in top if w / s > 0.01}
            for vv2 in (vset if tris(P) <= RIGID else [v]):
                W[vv2.index] = ws_; n += 1
groups = {g.name: g for g in body.vertex_groups}
idx = list(W)
for g in body.vertex_groups:
    if g.name in BONES: g.remove(idx)
for i, ws in W.items():
    for k2, w in ws.items(): groups[k2].add([i], w, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('LEAFWEIGHTS', {'parts': len(targets), 'verts': n, 'carrier_faces': len(carrier_faces)})
