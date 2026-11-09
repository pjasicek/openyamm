"""Stride of locomotion actions on our body (gait2, 2026-10-21): planted-foot backward speed x cycle, as measure_stride.py
(ankle joints while the shoe is within 2.5 cm of its lowest), plus the pelvis height range and the lowest shoe point.
Args: -- <blend> <action> [<action> ...]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
r = bpy.data.objects['Rig']; b = bpy.data.objects['Body']; sc = bpy.context.scene; sc.render.fps = 30
co = np.array([tuple(v.co) for v in b.data.vertices]); pc = np.array([v.value for v in b.data.attributes['piece'].data])
for role in a[1:]:
    act = bpy.data.actions[role]; r.animation_data_create(); r.animation_data.action = act
    if act.slots: r.animation_data.action_slot = act.slots[0]
    points = []; floors = []; pel = []
    for f in range(int(act.frame_range[1]) + 1):
        sc.frame_set(f); points.append([tuple(r.pose.bones['B_' + s + '_Foot'].head) for s in 'LR'])
        pel.append(r.pose.bones['B_Pelvis'].head.z)
        ev = b.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
        floors.append([float(z[(pc == 12) & (co[:, 0] * sign > 0)].min()) for sign in [1, -1]])
    points = np.array(points); floors = np.array(floors); vel = np.diff(points[:, :, 1], axis=0) * 30
    near = floors[:-1] < floors.min(axis=0) + .025; samples = vel[near & (vel > .02)]
    speed = float(np.median(samples)) if len(samples) > 3 else float('nan'); duration = act.frame_range[1] / 30
    print('GAIT2_STRIDE', json.dumps({'action': role, 'duration_s': duration, 'stance_speed_m_s': round(speed, 3),
          'stride_m': round(speed * duration, 3), 'samples': int(len(samples)), 'planted_share': round(float(near.mean()), 2),
          'pelvis_z': [round(min(pel), 3), round(max(pel), 3)], 'shoe_low_m': round(float(floors.min()), 4)}))
