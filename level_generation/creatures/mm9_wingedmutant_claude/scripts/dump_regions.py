"""Bind-pose triangles (UV, region) of a mesh -> npz, region from the bones weighting each triangle.

Args: <blend|glb> <out npz> <object name prefix>
Region per vertex by its dominant bone: 1 skin (calves, feet, claws, toes, tail), 5 head
(Bip01 Head, Neck1: face skin or scalp hair, split by brightness in compose.py), 2 feathers (pelvis,
spine, neck, thighs), 3 wing (Yw*), 4 hair (Xhair*); a triangle takes its vertices' majority.
"""
import bpy, sys
import numpy as np
from collections import Counter

argv = sys.argv[sys.argv.index('--') + 1:]
src, out, name = argv
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    if arm.animation_data:
        arm.animation_data.action = None
    for b in arm.pose.bones:
        b.matrix_basis.identity()


def region(b):
    if b.startswith('Yw'):
        return 3
    if b.startswith('Xhair'):
        return 4
    if b in ('Bip01 Head', 'Bip01 Neck1'):
        return 5
    if b in ('Bip01 Pelvis',) or b.startswith('Bip01 Spine') or b.startswith('Bip01 Neck') or 'Thigh' in b:
        return 2
    return 1


ob = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(name))
me = ob.data
me.calc_loop_triangles()
uv = me.uv_layers.active.data
gn = {g.index: g.name for g in ob.vertex_groups}
reg = [region(gn[max(v.groups, key=lambda g: g.weight).group]) if v.groups else 1 for v in me.vertices]
U, R, X = [], [], []
for t in me.loop_triangles:
    U.append([tuple(uv[l].uv) for l in t.loops])
    R.append(Counter(reg[v] for v in t.vertices).most_common(1)[0][0])
    X.append([tuple(ob.matrix_world @ me.vertices[v].co) for v in t.vertices])
np.savez(out, uv=np.array(U, np.float32), region=np.array(R, np.int32), xyz=np.array(X, np.float32))
print('DUMPED', len(U), Counter(R))
