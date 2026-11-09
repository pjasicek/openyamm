"""Scale Meshy body to MM9's height, dump joint list and symmetry; silhouette overlay front/side. Args: <mm9 glb> <meshy glb> <out dir>"""
import bpy, sys, json, os
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
MM9, MESHY, OUT = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
M = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')]
dg = bpy.context.evaluated_depsgraph_get()
A = []
for o in M:
    me = o.evaluated_get(dg).to_mesh(); A += [tuple(o.matrix_world @ v.co) for v in me.vertices]
A = np.array(A)
print('MM9 mesh bbox', A.min(0), A.max(0), 'verts', len(A), [o.name for o in M])
for k, v in J.items(): print('J %-22s %s' % (k, np.round(v, 3)))
# symmetry of MM9 upper body
up = A[A[:, 2] > -0.1]
from mathutils.kdtree import KDTree
kd = KDTree(len(up))
for i, p in enumerate(up): kd.insert(p, i)
kd.balance()
d = [kd.find((-p[0], p[1], p[2]))[2] for p in up]
print('MM9 upper mirror residual mean %.4f p90 %.4f max %.4f' % (np.mean(d), np.percentile(d, 90), np.max(d)))
bpy.ops.import_scene.gltf(filepath=MESHY)
o = [x for x in bpy.data.objects if x.type == 'MESH' and x.name.startswith('mesh')][0]
P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
s = np.ptp(A[:, 2]) / np.ptp(P[:, 2])
print('scale', s, 'ours h', np.ptp(P[:, 2]), 'mm9 h', np.ptp(A[:, 2]))
P = P * s; P[:, 2] += A[:, 2].min() - P[:, 2].min()
m = (P[:, 2] > 0.0) & (P[:, 2] < 0.4) & (np.abs(P[:, 0]) < 0.12); ma = (A[:, 2] > 0.0) & (A[:, 2] < 0.4) & (np.abs(A[:, 0]) < 0.12)
P[:, 1] += 0.5 * (A[ma, 1].min() + A[ma, 1].max()) - 0.5 * (P[m, 1].min() + P[m, 1].max())
P[:, 0] -= 0.5 * (P[:, 0].min() + P[:, 0].max()) - 0.5 * (A[:, 0].min() + A[:, 0].max())
print('ours bbox', P.min(0), P.max(0))
up = P[(P[:, 2] > -0.1)]
kd = KDTree(len(up))
for i, p in enumerate(up): kd.insert(p, i)
kd.balance()
d = [kd.find((-p[0], p[1], p[2]))[2] for p in up]
print('ours upper mirror residual mean %.4f p90 %.4f max %.4f' % (np.mean(d), np.percentile(d, 90), np.max(d)))
np.savez(os.path.join(OUT, 'fit_cmp.npz'), A=A, P=P)
