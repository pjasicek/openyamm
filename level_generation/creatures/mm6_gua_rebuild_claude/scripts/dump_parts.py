"""Dump the coif-repaired Smart Topology parts (vertices, faces, part index, connected component) and the MM9 guard's rest mesh/joints to npz.
Args: <st1r blend> <mm9 true glb> <out npz>"""
import bpy, sys
import numpy as np
SRC, MM9, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name.startswith('guard'))
mp = np.array([tuple(mesh_b.matrix_world @ v.co) for v in mesh_b.data.vertices])
jn = [b.name for b in arm.data.bones]; jp = np.array([tuple(arm.matrix_world @ b.head_local) for b in arm.data.bones])
with bpy.data.libraries.load(SRC) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith('P')]
V, F, PI = [], [], []
off = 0
for o in dst.objects:
    q = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    V.append(q)
    for p in o.data.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            F.append([vs[0] + off, vs[k] + off, vs[k + 1] + off]); PI.append(int(o.name[1:]))
    off += len(q)
np.savez(OUT, V=np.concatenate(V), F=np.array(F), part=np.array(PI), mm9=mp, jn=np.array(jn), jp=jp)
print('DUMP', off, len(F))
