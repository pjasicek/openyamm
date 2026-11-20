import bpy, os, sys
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath('meshy/rig_v1/result_rigged_character_glb_url.glb'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); me = next(o for o in bpy.data.objects if o.type == 'MESH')
print('ARM scale', tuple(arm.scale), 'mesh', me.name, len(me.data.vertices))
for b in arm.data.bones:
    h = arm.matrix_world @ b.head_local
    print('BONE', b.name, b.parent.name if b.parent else '-', tuple(round(x, 3) for x in h))
co = np.array([tuple(me.matrix_world @ v.co) for v in me.data.vertices])
print('MESH bounds', co.min(0).round(3), co.max(0).round(3))
g = {x.index: x.name for x in me.vertex_groups}
# cloak-like verts: outer radius > 0.27 at z 0.3-0.8 (the cloak sides/back)
sel = [i for i in range(len(co)) if 0.2 < co[i, 2] < 0.8 and (abs(co[i, 0]) > 0.27 or co[i, 1] > 0.12)]
tot = {}
for i in sel:
    for e in me.data.vertices[i].groups:
        tot[g[e.group]] = tot.get(g[e.group], 0) + e.weight
print('CLOAK_LOWER weights', sorted(((round(v / len(sel), 3), k) for k, v in tot.items()), reverse=True)[:10])
