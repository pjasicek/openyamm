"""Lowest vertices by dominant bone at a clip frame. Args: blend mesh clip frame."""
import bpy, sys, os
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
mesh = bpy.data.objects[a[1]]; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions[a[2]]; bpy.context.scene.frame_set(int(a[3]))
vg = {g.index: g.name for g in mesh.vertex_groups}
dom = np.array([vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in mesh.data.vertices])
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
co = np.array([tuple(v.co) for v in ev.vertices])
for n in sorted(set(dom)):
    m = dom == n
    print('LOW', n, round(float(co[m, 2].min()), 4), round(float(np.median(co[m, 2])), 4))
