"""Right-palm facing per clip frame: palm normal from the hand bones (finger direction x knuckle line, signed so the
rest A-pose palm faces forward, as in the HD masters), expressed in the pelvis frame (x toward the body's centre line
for the right hand = 'inward', y forward, z up); plus the dagger axis (Dagger bone +Y) in the same frame.
Args: -- <blend> <out json> [action ...]"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
acts = a[2:] or ['Standing', 'Walking', 'Running', 'Hit', 'Fidget', 'Death']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
H = lambda n: np.array(rig.matrix_world @ rig.pose.bones[n].head)
def palm():
    f = H('B_R_Finger2') - H('B_R_Hand'); t = H('B_R_Finger1') - H('B_R_Finger4')
    n = np.cross(f, t); return n / np.linalg.norm(n)
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
sign = 1.0 if palm() @ np.array([0, -1, 0]) > 0 else -1.0
res = {'sign': sign}
for name in acts:
    if name not in bpy.data.actions: continue
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); rows = []
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 8)):
        bpy.context.scene.frame_set(f)
        M = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).to_3x3().normalized()
        fwd = np.array(M @ Vector((0, -1, 0))) if True else None
        # pelvis frame from the rest: forward -Y, right hand inward = +X
        R = np.array(M) @ np.array(rig.data.bones['B_Pelvis'].matrix_local.to_3x3().normalized()).T
        loc = lambda v: R.T @ v
        p = loc(palm() * sign)
        d = None
        if 'Dagger' in rig.pose.bones:
            d = loc(np.array((rig.matrix_world @ rig.pose.bones['Dagger'].matrix).to_3x3() @ Vector((0, 1, 0))))
        rows.append({'frame': f, 'palm_inward': round(float(p[0]), 2), 'palm_forward': round(float(-p[1]), 2),
                     'palm_up': round(float(p[2]), 2), 'blade': None if d is None else [round(float(x), 2) for x in (d[0], -d[1], d[2])]})
    res[name] = rows
    print('PALM', name, ' '.join(f"f{r['frame']}:in{r['palm_inward']:+.2f}/fw{r['palm_forward']:+.2f}/up{r['palm_up']:+.2f}" for r in rows))
json.dump(res, open(out, 'w'), indent=1)
