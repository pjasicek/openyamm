"""Foot contact probe on the skinned mesh: per action and frame, the lowest point of each foot (vertices weighted
> 0.5 to Foot/Toe) and the lowest heel / toe-tip points, against the floor z = 0. Prints per action the range of the
lowest sole height and the frames where a foot that should stand is above 1 cm or below -0.5 cm.
Args: -- <blend> <action> [...]  (env STEP=0.5 for half frames)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); acts = a[1:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
FOOT = {s: np.array([sum(e.weight for e in v.groups if names[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5 for v in me.vertices]) for s in 'LR'}
step = float(os.environ.get('STEP', '1'))
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; rows = []
    for f in np.arange(f0, f1 + 1e-6, step):
        sc.frame_set(int(f), subframe=float(f - int(f)))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
        rows.append((f, z[FOOT['L']].min(), z[FOOT['R']].min()))
    R = np.array(rows)
    low = np.minimum(R[:, 1], R[:, 2])
    print(f'SOLE {an}: lowest foot per frame min {low.min() * 100:.1f} max {low.max() * 100:.1f} cm; '
          f'L {R[:, 1].min() * 100:.1f}..{R[:, 1].max() * 100:.1f} R {R[:, 2].min() * 100:.1f}..{R[:, 2].max() * 100:.1f}; '
          f'frames with both feet > 1 cm: {[round(x, 1) for x in R[low > 0.01, 0]][:12]}')
