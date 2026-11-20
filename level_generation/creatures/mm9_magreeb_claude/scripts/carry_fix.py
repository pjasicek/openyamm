"""Carry a later fit correction onto the textured (reduced + UV'd) mesh without changing its UVs or weights.

Args: <uv blend> <old fit blend> <new fit blend> <out blend> <report json>
The two fits come from the same Meshy mesh (same vertex order), so new - old is a per-vertex displacement field;
each vertex of the reduced 'Body' takes the inverse-distance blend of the displacements of its 4 nearest old-fit
vertices (bind pose). Used for fit v6 (straight feet, no fin on the forked front feet) onto the retextured v5 mesh.
"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
UV, OLD, NEW, OUT, REP = argv


def body_positions(path):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.meshes = ['Body']
    me = dst.meshes[0]
    P = np.array([tuple(v.co) for v in me.vertices])
    bpy.data.meshes.remove(me)
    return P


bpy.ops.wm.open_mainfile(filepath=UV)
old = body_positions(OLD)
new = body_positions(NEW)
assert old.shape == new.shape
disp = new - old
k = KDTree(len(old))
for i, p in enumerate(old):
    k.insert(Vector(p), i)
k.balance()
body = bpy.data.objects['Body']
moved, worst = 0, 0.0
for v in body.data.vertices:
    near = k.find_n(v.co, 4)
    w = np.array([1.0 / max(d, 1e-5) for _, _, d in near])
    d = sum(disp[i] * wi for (_, i, _), wi in zip(near, w)) / w.sum()
    n = float(np.linalg.norm(d))
    if n > 1e-5:
        v.co = v.co + Vector(d)
        moved += 1
        worst = max(worst, n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep = {'moved': moved, 'max_move': worst, 'verts': len(body.data.vertices)}
json.dump(rep, open(REP, 'w'))
print('CARRY', rep)
