"""Constant floor lift (7m452 review 2026-10-20: "soles about 2 cm below the floor in Standing"): the retargeted idle
keeps the source body's feet 1.5-1.9 cm under the floor, and Standing gets no floor pass (clip_timing.py passes the hit,
fidget and death per frame and lifts the walk). Per listed clip, one constant pelvis shift that puts the median of the
per-frame lowest sole (vertices weighted > 0.5 to the feet/toes) on the floor. Runs before clip_timing.py, so the
one-shots blend from the corrected Standing pose. Args: -- <in> <out> <Action> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
vg = [g.name for g in body.vertex_groups]
FEET = np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')) > 0.5
                 for v in body.data.vertices])
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); lows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear(); lows.append(z[FEET].min())
    lift = -float(np.median(lows))
    pb = rig.pose.bones['B_Pelvis']; pb.rotation_mode = 'QUATERNION'
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        M = rig.matrix_world @ pb.matrix; M.translation.z += lift
        pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
        pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'FLOOR {name}: lowest sole {min(lows) * 100:.1f}..{max(lows) * 100:.1f} cm, constant lift {lift * 100:.1f} cm')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
