"""Lowest vertices of the posed body at ACTION@FRAME: dominant bone and z. Args: blend action@frame [n]"""
import bpy, sys
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.modifiers and o.name in ('Body', 'DragonKing'))
name, f = argv[1].split('@')
arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[name]
try:
    arm.animation_data.action_slot = bpy.data.actions[name].slots[0]
except Exception:
    pass
bpy.context.scene.frame_set(int(f))
dg = bpy.context.evaluated_depsgraph_get()
me = body.evaluated_get(dg).to_mesh()
vg = {g.index: g.name for g in body.vertex_groups}
zs = sorted(((body.matrix_world @ v.co).z, i) for i, v in enumerate(me.vertices))
n = int(argv[2]) if len(argv) > 2 else 40
c = Counter(vg[max(body.data.vertices[i].groups, key=lambda g: g.weight).group] for z, i in zs[:n])
print('LOWEST', round(zs[0][0], 3), c.most_common(8))
for thr in (-0.4, -0.2, 0.0):
    c2 = Counter(vg[max(body.data.vertices[i].groups, key=lambda g: g.weight).group] for z, i in zs if z < thr)
    print('BELOW', thr, sum(c2.values()), c2.most_common(6))
