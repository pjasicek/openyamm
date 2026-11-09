"""Use the attack's idle lead-in for its existing raise, retaining the final draw and release timing."""
import bpy
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
LEAD = 13.0
JOIN = 22.0


def curves(action):
    return [fc for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for fc in bag.fcurves]


def signature(action):
    data = [(fc.data_path, fc.array_index, [(tuple(k.co), k.interpolation) for k in fc.keyframe_points])
            for fc in curves(action)]
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()


report = {}
for relative in ['work/textured_uv.blend', 'export/m628_master.blend']:
    path = P / relative
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    assert not scene.get('attack_opening_retimed'), 'Already corrected; use the retained v2 checkpoint to replay.'
    rig = bpy.data.objects['Rig']
    attack = bpy.data.actions['Attack']
    rig.animation_data.action = attack
    rig.animation_data.action_slot = attack.slots[0]
    other = {a.name: signature(a) for a in bpy.data.actions if a != attack}
    times = [i / 4 for i in range(149)]

    def pose(frame):
        scene.frame_set(int(frame), subframe=frame % 1)
        return [tuple(value for row in bone.matrix for value in row) for bone in rig.pose.bones]

    expected = {f: pose(LEAD + f * (JOIN - LEAD) / JOIN if f < JOIN else f) for f in times}
    before = signature(attack)
    for fc in curves(attack):
        assert all(k.interpolation == 'LINEAR' for k in fc.keyframe_points)
        values = {float(k.co.x): float(k.co.y) for k in fc.keyframe_points if k.co.x >= LEAD}
        values[LEAD] = fc.evaluate(LEAD)
        values[JOIN] = fc.evaluate(JOIN)
        while fc.keyframe_points:
            fc.keyframe_points.remove(fc.keyframe_points[-1], fast=True)
        fc.keyframe_points.add(len(values))
        for key, (frame, value) in zip(fc.keyframe_points, sorted(values.items())):
            key.co = ((frame - LEAD) * JOIN / (JOIN - LEAD) if frame < JOIN else frame, value)
            key.interpolation = 'LINEAR'
        fc.update()
    error = max(abs(a - b) for f in times for actual, wanted in zip(pose(f), expected[f])
                for a, b in zip(actual, wanted))
    assert error < 0.00003, error
    assert other == {a.name: signature(a) for a in bpy.data.actions if a != attack}
    assert tuple(attack.frame_range) == (0.0, 37.0)
    assert abs(float(scene['attack_impact_seconds']) - 27.5 / 30) < 1e-7
    # Visible bow-hand movement in the opening catches the original idle block returning.
    scene.frame_set(0)
    start = rig.pose.bones['B_L_Hand'].head.copy()
    opening = []
    for f in [3, 6, 9, 13, 18, 21]:
        scene.frame_set(f)
        opening.append({'frame_30fps': f, 'hand_travel_m': (rig.pose.bones['B_L_Hand'].head - start).length})
    assert opening[1]['hand_travel_m'] > 0.015, opening
    scene['attack_opening_retimed'] = 'v3: source 13..22 -> 0..22; frame 22 and later unchanged'
    rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.matrix_basis.identity()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    report[relative] = {'before': before, 'after': signature(attack), 'max_pose_matrix_error': error,
                        'unchanged_actions': other, 'opening': opening}

(P / 'work/attack_opening_retime.json').write_text(json.dumps({
    'source_lead_frames_30fps': LEAD, 'join_frame_30fps': JOIN, 'release_frame_30fps': 27.5,
    'method': 'Linear stretch of existing raise across the idle lead-in; all channels use one time mapping.',
    'files': report}, indent=2) + '\n')
print(json.dumps(report, indent=2))
