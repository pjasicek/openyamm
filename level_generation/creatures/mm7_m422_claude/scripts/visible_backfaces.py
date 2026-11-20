"""Visible back faces from the front camera (what a double-sided material shows and the engine's back-face culling
hides as holes): per frame, faces whose posed normal points away from a front orthographic camera (-Y looking +Y)
and that are the first hit of a camera ray through their centroid. Reports count, area and their rest positions /
inner-layer flag (normal toward the body axis at rest). Args: -- <blend> <action> <frame,...> [view front|quarter]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
gv = np.array([x.value for x in me.attributes['garment'].data]); rest = np.array([v.co[:] for v in me.vertices])
pel = np.array(rig.data.bones['B_Pelvis'].head_local)
F = [tuple(p.vertices) for p in me.polygons]
def nrm(P, f):
    v = P[list(f)]; n = np.cross(v[1] - v[0], v[2] - v[0]); return n / (np.linalg.norm(n) + 1e-12), np.linalg.norm(n) / 2
inner0 = []
for f in F:
    n, _ = nrm(rest, f); c = rest[list(f)].mean(0); r = c - pel; r[2] = 0
    inner0.append(np.linalg.norm(r) > 1e-4 and n @ (r / np.linalg.norm(r)) < -0.2)
inner0 = np.array(inner0)
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
ang = math.radians(35 if len(a) > 3 and a[3] == 'quarter' else 0)
V = Vector((math.sin(ang), math.cos(ang), 0))            # view direction (camera looks along +V)
for fr in [int(x) for x in a[2].split(',')]:
    bpy.context.scene.frame_set(fr)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
    T = BVHTree.FromPolygons([tuple(x) for x in P], F)
    vis = []
    for i, f in enumerate(F):
        if gv[f[0]] not in (1, 2, 8, 15):
            continue
        n, ar = nrm(P, f)
        if n @ np.array(V) <= 0.05:
            continue
        c = Vector(P[list(f)].mean(0)); o = c - V * 3
        h = T.ray_cast(o, V, 4)
        if h[0] is not None and h[2] == i:
            vis.append((i, ar))
    if not vis:
        print('BACKVIS', a[1], fr, 0); continue
    idx = np.array([v[0] for v in vis]); area = sum(v[1] for v in vis)
    rc = np.array([rest[list(F[i])].mean(0) for i in idx])
    print('BACKVIS', a[1], fr, 'faces', len(idx), 'area cm2', round(area * 1e4, 1), 'inner-layer share', round(float(inner0[idx].mean()), 2),
          'garments', {int(g): int((gv[[F[i][0] for i in idx]] == g).sum()) for g in (1, 2, 8, 15)},
          'rest z', np.round(np.percentile(rc[:, 2], [10, 50, 90]), 2).tolist(), 'rest x', np.round(np.percentile(rc[:, 0], [10, 50, 90]), 2).tolist())
