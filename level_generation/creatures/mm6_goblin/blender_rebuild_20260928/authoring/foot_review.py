"""Audit foot orientation and sole clearance in the actual baked walk at half-frame intervals."""
import json
import math

import bpy
from mathutils import Vector

import motion
import pose
from mesh_tools import ROOT


def audit(imported=False, output=None):
    if imported:
        import roundtrip
        arm = roundtrip.activate_import('walk', 1)
        scene = bpy.data.scenes['GB15 Export validation']
        objects = list(scene.objects)
    else:
        scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
        bpy.context.window.scene = scene
        motion.activate('walk')
        arm = pose.rig()
        objects = list(bpy.data.collections['GB15 Character'].objects)
    foot_vertices = {suffix: [] for suffix in ['.L', '.R']}
    for suffix in foot_vertices:
        for obj in objects:
            if obj.type != 'MESH' or 'foot' + suffix not in obj.vertex_groups:
                continue
            group = obj.vertex_groups['foot' + suffix].index
            indices = [v.index for v in obj.data.vertices
                       if any(g.group == group and g.weight > .99 for g in v.groups)]
            if indices:
                foot_vertices[suffix].append((obj, indices))
    records, joints = [], []
    for step in range(97):
        scene.frame_set(1 + step // 2, subframe=(step % 2) * .5)
        graph = bpy.context.evaluated_depsgraph_get()
        record = {'time': step / 96, 'feet': {}}
        joints.append({bone.name: list(bone.head) for bone in arm.pose.bones})
        for suffix, shift in motion.WALK_PHASES:
            foot = arm.pose.bones['foot' + suffix]
            delta = arm.matrix_world @ foot.matrix @ foot.bone.matrix_local.inverted() @ arm.matrix_world.inverted()
            forward = delta.to_3x3() @ Vector((0, -1, 0))
            right = delta.to_3x3() @ Vector((1, 0, 0))
            points = []
            for obj, indices in foot_vertices[suffix]:
                evaluated = obj.evaluated_get(graph)
                points.extend(evaluated.matrix_world @ evaluated.data.vertices[i].co for i in indices)
            record['feet'][suffix] = {
                'phase': (step / 96 + shift) % 1,
                'pitch_toes_up_degrees': math.degrees(math.atan2(forward.z, -forward.y)),
                'yaw_degrees': math.degrees(math.atan2(forward.x, -forward.y)),
                'roll_degrees': math.degrees(math.asin(max(-1, min(1, right.z)))),
                'sole_clearance_m': min(point.z for point in points), 'ankle': list(foot.head)}
        records.append(record)
    stats = {}
    for suffix in foot_vertices:
        feet = [record['feet'][suffix] for record in records]
        stance = [foot['sole_clearance_m'] for foot in feet if foot['phase'] <= motion.WALK_STANCE]
        stats[suffix] = {
            'pitch_range_degrees': [min(f['pitch_toes_up_degrees'] for f in feet),
                                    max(f['pitch_toes_up_degrees'] for f in feet)],
            'stance_clearance_range_m': [min(stance), max(stance)],
            'maximum_swing_clearance_m': max(f['sole_clearance_m'] for f in feet),
            'maximum_abs_yaw_degrees': max(abs(f['yaw_degrees']) for f in feet),
            'maximum_abs_roll_degrees': max(abs(f['roll_degrees']) for f in feet)}
        assert min(stance) >= -.0001 and max(stance) < .004, stats[suffix]
        assert min(f['sole_clearance_m'] for f in feet) >= -.0001
        assert stats[suffix]['pitch_range_degrees'][0] < -35
        assert stats[suffix]['pitch_range_degrees'][1] > 24
        assert stats[suffix]['maximum_abs_yaw_degrees'] < .1
        assert stats[suffix]['maximum_abs_roll_degrees'] < .1
    closure = max((Vector(joints[0][name]) - Vector(joints[-1][name])).length for name in joints[0])
    assert closure < .00001
    report = {'status': 'pass', 'source': 'reimported GLB' if imported else 'authored Blender action',
              'sample_fps': 96, 'samples': len(records), 'feet': stats,
              'all_joint_loop_error_m': closure,
              'native_observation': 'b/e: toes-up landing. c/f: heel raised behind the body. Front: no wide splay.',
              'interpretation': '26 degree landing, 38 degree push-off; estimates, not measured native 3D angles.',
              'scope': 'Rigid foot bones; no new toe articulation. Two millimeter nominal sole clearance.'}
    receipt = 'foot_export_validation.json' if imported else 'foot_validation.json'
    measurements = 'feet_export_subframes.json' if imported else 'feet_after_subframes.json'
    (ROOT / 'delivery' / receipt).write_text(json.dumps(report, indent=2) + '\n')
    output = output or ROOT / 'review/body_motion_correction'
    (output / measurements).write_text(
        json.dumps(records, indent=2) + '\n')
    if imported:
        roundtrip.activate_import('standing', 1)
    else:
        motion.activate('standing')
    print(json.dumps(report, indent=2))
    return report
