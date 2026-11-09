"""Move the existing UV-mapped hilt onto the palm side without rebuilding the character."""
import json

import bpy
from mathutils import Vector

from mesh_tools import ROOT


def migrate():
    arm = bpy.data.objects['GB15 Goblin rig']
    assert bpy.context.scene.get('gb_owner') == str(ROOT)
    if arm.get('gb_hand_revision') == 1:
        return
    arm.animation_data.action = None
    shift = Vector((0, .05, 0))
    sword = bpy.data.objects['GB15 Curved sword']
    for vertex in sword.data.vertices:
        vertex.co += shift
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    weapon = arm.data.edit_bones['weapon.R']
    weapon.head += shift
    weapon.tail += shift
    bpy.ops.object.mode_set(mode='OBJECT')
    path = ROOT / 'authoring/weapon.json'
    info = json.loads(path.read_text())
    info['center'] = list(Vector(info['center']) + shift)
    info['palm_side'] = 'Bind +Y; hand local -Z. Negative local X flexion.'
    path.write_text(json.dumps(info, indent=2) + '\n')
    arm['gb_hand_revision'] = 1
    bpy.context.view_layer.update()
    print('Moved sword bind geometry and attachment 50 mm onto the palm side; UVs unchanged.')


def check():
    """Check the reported palm-side error and fixed attachment across baked action samples."""
    import motion

    arm = bpy.data.objects['GB15 Goblin rig']
    motion.activate('standing')
    standing = {}
    for suffix, inward in [('.R', Vector((1, 0, 0))), ('.L', Vector((-1, 0, 0)))]:
        hand = arm.pose.bones['hand' + suffix]
        rotation = hand.matrix.to_quaternion()
        palm = rotation @ Vector((0, 0, -1))
        thumb = rotation @ Vector((-1 if suffix == '.R' else 1, 0, 0))
        standing[suffix] = {'palm_dot_inward': palm.dot(inward),
                            'thumb_dot_forward': thumb.dot(Vector((0, -1, 0)))}
        assert standing[suffix]['palm_dot_inward'] > .95, standing
        assert standing[suffix]['thumb_dot_forward'] > .9, standing
    rest_center = arm.data.bones['hand.R'].matrix_local.inverted() @ arm.data.bones['weapon.R'].head_local
    assert rest_center.z < -.020, rest_center
    samples = []
    for name, duration, spacing, function in motion.CLIPS:
        for fraction in [0, .25, .5, .75, 1]:
            frame = round(duration * 48 * fraction) + 1
            motion.activate(name, frame)
            hand = arm.pose.bones['hand.R']
            center = hand.matrix.inverted() @ arm.pose.bones['weapon.R'].head
            error = (center - rest_center).length
            assert error < .00001, (name, frame, error)
            palm = hand.matrix.to_quaternion() @ Vector((0, 0, -1))
            flexion = min(arm.pose.bones[f'digit.R.{i}.01'].vector.normalized().dot(palm) for i in range(4))
            assert flexion > .85, (name, frame, flexion)
            left_hand = arm.pose.bones['hand.L']
            thumb_tip = left_hand.matrix.inverted() @ arm.pose.bones['thumb.L.03'].tail
            assert thumb_tip.z < -.015 and thumb_tip.x > .035, (name, frame, list(thumb_tip))
            neutral_offset = None
            if name == 'standing':
                neutral_offset = max(abs(arm.pose.bones[bone].head.x) for bone in ['chest', 'neck', 'head'])
                assert neutral_offset < .000002, (frame, neutral_offset)
            samples.append({'clip': name, 'frame': frame, 'attachment_error_m': error,
                            'minimum_finger_flexion_dot_palm': flexion,
                            'left_thumb_tip_in_hand_m': list(thumb_tip),
                            'standing_neck_head_lateral_offset_m': neutral_offset})
    report = {'status': 'pass', 'standing': standing, 'samples': samples,
              'scope': ('Palm/thumb direction, finger flexion, hilt attachment, relaxed left thumb and '
                        'neutral neck/head centering; not a full collision audit.')}
    (ROOT / 'delivery/hand_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    motion.activate('standing')
    print('Hand-side validation passed;', len(samples), 'action samples')
    return report


if __name__ == '__main__':
    migrate()
