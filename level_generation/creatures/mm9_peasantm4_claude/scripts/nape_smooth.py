"""Smooth away the ponytail root knot that Forad's Meshy head carries at the nape (after strip_parts.py removed the
ponytail): Laplacian smoothing of the main mesh's vertices inside an ellipsoid round the knot, weight 1 in the core
fading to 0 at the rim; vertex moves only (no topology, UV or weight change). Args (Blender): <in blend> <out blend>
<report json> [cx cy cz rx ry rz iters]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
cx, cy, cz, rx, ry, rz, IT = [float(x) for x in a[3:10]] if len(a) >= 10 else (-0.017, 0.10, 0.675, 0.05, 0.05, 0.045, 30)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = body.data; mw = body.matrix_world; inv = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
P = np.array([mw @ v.co for v in bm.verts])
r = np.sqrt(((P[:, 0] - cx) / rx) ** 2 + ((P[:, 1] - cy) / ry) ** 2 + ((P[:, 2] - cz) / rz) ** 2)
w = np.clip((1.0 - r) / 0.4, 0, 1); w = w * w * (3 - 2 * w)
w[P[:, 1] < 0.02] = 0                      # back of the head only
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
Q = P.copy(); act = np.where(w > 0)[0]
for _ in range(int(IT)):
    N = Q.copy()
    for i in act:
        if nb[i]: N[i] = Q[i] + 0.5 * w[i] * (Q[nb[i]].mean(0) - Q[i])
    Q = N
D = np.linalg.norm(Q - P, axis=1)
for i in act: bm.verts[i].co = inv @ Vector(Q[i])
bm.to_mesh(me); bm.free(); me.update()
rep = dict(moved=int((D > 1e-5).sum()), max_cm=float(D.max() * 100), p90_cm=float(np.percentile(D[act], 90) * 100) if len(act) else 0)
json.dump(rep, open(REP, 'w'), indent=1); print('NAPE', rep)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
