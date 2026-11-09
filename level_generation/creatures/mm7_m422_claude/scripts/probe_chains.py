"""Distance of each robe chain joint (posed) to the leg segments (hip-knee, knee-ankle) at one frame, and of the posed
skin of the leg to the nearest skirt vertex. Args: -- <blend> <action> <frame>"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2]))
J = lambda n, t=False: np.array(rig.matrix_world @ (rig.pose.bones[n].tail if t else rig.pose.bones[n].head))
def sd(p, x, y):
    ab = y - x; t = np.clip((p - x) @ ab / (ab @ ab), 0, 1); return np.linalg.norm(p - (x + t * ab))
segs = {s: [(J(f'B_{s}_Thigh'), J(f'B_{s}_Calf')), (J(f'B_{s}_Calf'), J(f'B_{s}_Foot'))] for s in 'LR'}
CH = json.loads(bpy.context.scene['cloak_chains'])
for c in CH:
    pts = [J(b) for b in c['bones']] + [J(c['bones'][-1], True)]
    out = []
    for p in pts:
        d = min(sd(p, x, y) for s in 'LR' for x, y in segs[s])
        out.append(f'z{p[2]:.2f}:{d * 100:.0f}')
    print('CHAIN', round(c['deg']), ' '.join(out))
body = bpy.data.objects['Body']; ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
gv = np.array([x.value for x in body.data.attributes['garment'].data])
print('HIPS', {s: np.round(segs[s][0][0], 3).tolist() for s in 'LR'}, 'knees', {s: np.round(segs[s][0][1], 3).tolist() for s in 'LR'})
