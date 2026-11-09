"""Verify continuous hand motion and whole-body participation during channeling."""
import bpy, json, math
from pathlib import Path
P = Path(__file__).resolve().parents[1]
report = {}
names = ['B_Pelvis', 'B_Spine2', 'B_Head', 'B_L_Thigh', 'B_R_Thigh',
         'B_L_Calf', 'B_R_Calf', 'B_L_Hand', 'B_R_Hand']
def angle(a, b):
    return math.degrees(2 * math.acos(min(1, abs(a.normalized().dot(b.normalized())))))
for label, path in [('before', 'review/dual_cast_v6/work/master_settled.blend'),
                    ('authored', 'work/master_settled.blend'), ('export', 'export/mm8_m420_prepared.glb')]:
    if path.endswith('.blend'):
        bpy.ops.wm.open_mainfile(filepath=str(P / path))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps = 30
        bpy.ops.import_scene.gltf(filepath=str(P / path))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    sc = bpy.context.scene
    report[label] = {}
    for role in ['Attack', 'Cast']:
        action = bpy.data.actions[role]
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        poses = []
        for frame in range(85):
            f = frame / 48 * sc.render.fps
            sc.frame_set(math.floor(f), subframe=f % 1)
            poses.append({name: (rig.matrix_world @ rig.pose.bones[name].matrix).copy() for name in names})
        steps = [{side: (b[f'B_{side}_Hand'].translation - a[f'B_{side}_Hand'].translation).length * 1000
                  for side in 'LR'} for a, b in zip(poses, poses[1:])]
        minimum = {side: min(row[side] for row in steps[29:36]) for side in 'LR'}
        body = {}
        for name in names[:7]:
            body[name] = {
                'first_36_frames_displacement_mm': max((pose[name].translation - poses[0][name].translation).length * 1000
                                                       for pose in poses[:37]),
                'first_36_frames_rotation_deg': max(angle(pose[name].to_quaternion(), poses[0][name].to_quaternion())
                                                    for pose in poses[:37]),
                'max_step_deg_per_48fps': max(angle(b[name].to_quaternion(), a[name].to_quaternion())
                                              for a, b in zip(poses, poses[1:]))}
        checkpoints = {frame: (poses[frame]['B_Pelvis'].translation - poses[0]['B_Pelvis'].translation).length * 1000
                       for frame in [8, 16, 24, 36]}
        report[label][role] = {'frames_29_36_minimum_step_mm': minimum, 'body_motion': body,
                              'pelvis_displacement_mm_at_frame': checkpoints, 'hand_steps_mm': steps}
        if label != 'before':
            assert min(minimum.values()) > 0.5, (label, role, minimum)
            assert body['B_Pelvis']['first_36_frames_displacement_mm'] > 25, (label, role, body)
            assert body['B_Spine2']['first_36_frames_rotation_deg'] > 5, (label, role, body)
            for name in ['B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf']:
                assert body[name]['first_36_frames_rotation_deg'] > 5, (label, role, name, body[name])
            assert all(value > .5 for value in checkpoints.values()), (label, role, checkpoints)
            assert max(value['max_step_deg_per_48fps'] for value in body.values()) < 12, (label, role, body)
(P / 'review/dual_cast/windup.json').write_text(json.dumps(report, indent=2) + '\n')
print('CHANNEL', json.dumps({label: {role: row['body_motion'] for role, row in roles.items()}
                             for label, roles in report.items()}), flush=True)
