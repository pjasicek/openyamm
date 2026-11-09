"""hkr bulk check: the front silhouette's shoulder width (body + armour, the widest x extent over z 1.25-1.60: across
the pauldrons) against its hip width (z 0.70-0.95, arm, hand and finger skin, the forearm guards and the buckler left
out: the arms hang there), Standing frame 0, metres. Concept fam_troopers.png (front and back views): 1.15.
Args: -- <blend> [clip frame]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; body = bpy.data.objects['Body']
clip, fr = (a[1], int(a[2])) if len(a) > 2 else ('Standing', 0)
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc.frame_set(fr)


def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


GI = {g.index: g.name for g in body.vertex_groups}
DOM = np.array([GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices])
armv = np.array([any(t in d for t in ('Forearm', 'Hand', 'Finger')) for d in DOM])
B = ev(body)
arm_obs = [o for o in bpy.data.objects if o.name.startswith('Arm_') and not o.hide_render and 'carapace' not in o.name]
P = np.vstack([B] + [ev(o) for o in arm_obs])
H = np.vstack([B[~armv]] + [ev(o) for o in arm_obs if o.get('bone') not in ('B_L_Forearm', 'B_R_Forearm', 'B_L_Buckler')])
sh = P[(P[:, 2] > 1.25) & (P[:, 2] < 1.60)]; hp = H[(H[:, 2] > 0.70) & (H[:, 2] < 0.95)]
ws, wh = sh[:, 0].max() - sh[:, 0].min(), hp[:, 0].max() - hp[:, 0].min()
print('SILHOUETTE shoulders m', round(ws, 3), 'hips m', round(wh, 3), 'ratio', round(ws / wh, 2), '(concept 1.15)')
