"""Per frame of one action: each foot's lowest vertex z and its y relative to the ankle (heel > 0, toe < 0), and the
ankle height. Args: -- <blend> <action>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
vg = [g.name for g in body.vertex_groups]
W = {s: np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) for v in body.data.vertices]) > 0.5 for s in 'LR'}
for f in range(int(act.frame_range[1]) + 1):
    sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    row = []
    for s in 'LR':
        c = co[W[s]]; i = int(np.argmin(c[:, 2])); an = rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].head
        row.append(f'{s} low {100*c[i,2]:6.1f} dy {100*(c[i,1]-an.y):6.1f} ankle {100*an.z:5.1f}')
    print('FRAME', f, ' | '.join(row))
