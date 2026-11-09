"""Body = Meshy GLB with only a height scale and pelvis alignment, in the MM9 source scene, for joint estimation.
Args: <mm9 source blend> <meshy glb> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
SRC, MESHY, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']
A = np.array([tuple(o.matrix_world @ v.co) for o in bpy.data.objects if o.type == 'MESH' and 'trident' not in o.name for v in o.data.vertices])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
mo = next(o for o in new if o.type == 'MESH')
mo.name = 'Body'
for o in new:
    if o is not mo:
        bpy.data.objects.remove(o)
mo.parent = None
bpy.context.view_layer.objects.active = mo
mo.select_set(True)
M = np.array(mo.matrix_world)
P = np.array([v.co for v in mo.data.vertices]) @ M[:3, :3].T + M[:3, 3]
s = np.ptp(A[:, 2]) / np.ptp(P[:, 2])
P = P * s
P[:, 2] += A[:, 2].min() - P[:, 2].min()
P[:, 0] -= 0.5 * (P[:, 0].min() + P[:, 0].max())
for v, p in zip(mo.data.vertices, P):
    v.co = Vector(p)
from mathutils import Matrix
mo.matrix_world = Matrix.Identity(4)
print('SCALE', s, 'BB', P.min(0), P.max(0), 'MM9', A.min(0), A.max(0))
# slices
for z in np.arange(-0.6, 0.6, 0.05):
    m = np.abs(P[:, 2] - z) < 0.012
    m2 = np.abs(A[:, 2] - z) < 0.03
    e = lambda Q, k: (Q[k, 0].min(), Q[k, 0].max(), Q[k, 1].min(), Q[k, 1].max()) if k.any() else (0, 0, 0, 0)
    print('z %.2f ours x %.3f..%.3f y %.3f..%.3f | mm9 x %.3f..%.3f y %.3f..%.3f' % ((z,) + e(P, m) + e(A, m2)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
