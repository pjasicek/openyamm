"""Lowest posed vertices per dominant bone at one frame of an action. Args: -- <blend> <action> <frame>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); rig = bpy.data.objects['Rig']; m = bpy.data.objects['Body']
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
vn = [g.name for g in m.vertex_groups]
dom = np.array([vn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in m.data.vertices])
dg = bpy.context.evaluated_depsgraph_get(); ev = m.evaluated_get(dg); me = ev.to_mesh()
c = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', c); ev.to_mesh_clear(); z = c.reshape(-1, 3)[:, 2]
for n in sorted(set(dom), key=lambda n: z[dom == n].min())[:12]:
    print(f'LOW {n:12s} {z[dom == n].min():+.3f}')
