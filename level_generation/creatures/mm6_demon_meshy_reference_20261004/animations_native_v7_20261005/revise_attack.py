"""Extend the native Attack's right fingers in the image plane; retain the other motion."""
import importlib.util
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

STAGE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('motion', STAGE/'motion.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
rotate = motion.rotate
BASELINE = None
CHANGED_BONES = ['mixamorig:Right'+n for n in ('Arm', 'ForeArm', 'Hand')]
CHANGED_BONES += [f'mixamorig:RightHand{d}{i}' for d in ('Index', 'Middle', 'Pinky', 'Ring') for i in (1, 2, 3)]


def pose_at(clip, frame):
    assert clip == 'Attack' and BASELINE is not None
    scene, rig, mesh = motion.objects()
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    rig.animation_data.action = BASELINE
    rig.animation_data.action_slot = BASELINE.slots[0]
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    index, following = min(int(frame//6), 5), min(int(frame//6)+1, 5)
    u = max(0, min(1, (frame-index*6)/6))
    ease = u*u*(3-2*u)
    strength = [0, .55, 1, .70, .35, 0]
    amount = strength[index]*(1-ease)+strength[following]*ease
    upper = rig.pose.bones['mixamorig:RightArm']
    lower = rig.pose.bones['mixamorig:RightForeArm']
    hand = rig.pose.bones['mixamorig:RightHand']
    original_palm = sum((rig.pose.bones['mixamorig:RightHand'+d+'1'].head.copy()
                         for d in ('Index', 'Middle', 'Pinky', 'Ring')), Vector())/4-hand.head
    # A modest lift compensates for this model's taller head, without extending any bones.
    rotate(upper, Quaternion((0, 1, 0), math.radians(3*amount)))
    if amount > 0:
        current = hand.head-lower.head
        target = current.copy()
        target.z += .045*amount
        projected = math.hypot(target.x, target.z)
        if projected > current.length*.985:
            target.x *= current.length*.985/projected
            target.z *= current.length*.985/projected
        target.y = -math.sqrt(max(0, current.length**2-target.x**2-target.z**2))
        rotate(lower, current.rotation_difference(target))
    bases = [rig.pose.bones['mixamorig:RightHand'+d+'1'].head.copy()
             for d in ('Index', 'Middle', 'Pinky', 'Ring')]
    palm = sum(bases, Vector())/4-hand.head
    desired = original_palm.copy()
    desired.y *= 1-.80*amount
    rotate(hand, palm.rotation_difference(desired))
    direction = desired.normalized()
    # Native C has extended rays. Straighten both knuckles while keeping each terminal claw rigid.
    for digit, fan in [('Index', 9), ('Middle', 3), ('Pinky', -3), ('Ring', -9)]:
        first, second, third = [rig.pose.bones[f'mixamorig:RightHand{digit}{i}'] for i in (1, 2, 3)]
        ray = Quaternion((0, 1, 0), math.radians(fan)) @ direction
        correction = (second.head-first.head).rotation_difference(ray)
        rotate(first, Quaternion().slerp(correction, amount))
        correction = (third.head-second.head).rotation_difference(second.head-first.head)
        rotate(second, Quaternion().slerp(correction, amount))
        correction = (third.tail-third.head).rotation_difference(third.head-second.head)
        rotate(third, Quaternion().slerp(correction, .80*amount))
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        if bone.name != 'mixamorig:Hips':
            bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}


def build():
    global BASELINE
    scene, rig, mesh = motion.objects()
    original = next(t for t in rig.animation_data.nla_tracks if t.name == 'Attack')
    if BASELINE is None:
        BASELINE = original.strips[0].action
    sampled = motion.bake_action('Attack', pose=pose_at, end=36)
    action = BASELINE.copy()
    action.name = 'DemonNative_RightHand_Attack'
    target = action.layers[0].strips[0].channelbag(action.slots[0])
    sampled_curves = {(c.data_path, c.array_index): c
                      for c in sampled.layers[0].strips[0].channelbag(sampled.slots[0]).fcurves}
    paths = {f'pose.bones["{name}"].rotation_quaternion' for name in CHANGED_BONES}
    for curve in target.fcurves:
        if curve.data_path not in paths:
            continue
        new = sampled_curves[(curve.data_path, curve.array_index)]
        assert len(curve.keyframe_points) == len(new.keyframe_points) == 37
        for point, corrected in zip(curve.keyframe_points, new.keyframe_points):
            point.co = corrected.co
            point.interpolation = corrected.interpolation
        curve.update()
    revised_track = next(t for t in rig.animation_data.nla_tracks if t.name == 'Attack' and t != original)
    revised_track.strips[0].action = action
    revised_track.strips[0].action_slot = action.slots[0]
    rig.animation_data.nla_tracks.remove(original)
    rig.animation_data.action = None
    bpy.data.actions.remove(sampled)
    motion.activate('Attack', 12)
    bpy.data.libraries.write(str(STAGE/'authored_checkpoint.blend'), {scene}, fake_user=True, compress=True)
    return action
