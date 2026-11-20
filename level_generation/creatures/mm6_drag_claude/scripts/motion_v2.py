"""Revise only Attack/Cast on the accepted textured, reduced lizard master."""
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'mm6_rat_claude/scripts'))
import posing

baseline = P / 'work/accepted_v1.blend'
if not baseline.exists():
    shutil.copy2(P / 'export/mm6_drag.blend', baseline)
bpy.ops.wm.open_mainfile(filepath=str(baseline))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
scene = bpy.context.scene
scene.render.fps = 24
axes = {b.name: b.matrix_local.to_3x3().inverted() for b in rig.data.bones}
feet = {s: rig.data.bones[s + 'Foot'].head_local.copy() for s in ('L', 'R')}
footq = {s: rig.data.bones[s + 'Foot'].matrix_local.to_quaternion() for s in feet}


def action_hash(action):
    values = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    values.append((curve.data_path, curve.array_index,
                                   [(tuple(k.co), k.interpolation) for k in curve.keyframe_points]))
    return hashlib.sha256(repr(values).encode()).hexdigest()


preserved = {a.name: action_hash(a) for a in bpy.data.actions if a.name not in ('Attack', 'Cast')}


def smooth(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def envelopes(t, peak, release):
    # Continuous gathering and release, with no held windup plateau.
    prep = smooth(t / peak) * (1 - smooth((t - peak) / (release - peak)))
    hit = smooth((t - peak) / (release - peak)) * (1 - smooth((t - release) / (1.125 - release)))
    return prep, hit


def rotate(name, axis, angle):
    rig.pose.bones[name].rotation_quaternion @= Quaternion(axes[name] @ Vector(axis), angle)


def vertices():
    obj = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    result = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', result)
    obj.to_mesh_clear()
    return result.reshape(-1, 3)


def pose(name, t):
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.matrix_basis.identity()
    phase = t / 1.125 * math.tau
    prep, hit = envelopes(t, 10 / 24, .75)
    hipprep, hiphit = envelopes(t, 9 / 24, 17 / 24)
    side = 1 if name == 'Attack' else -.75
    pitch = .04 - .23 * hipprep + .38 * hiphit
    spine = -.12 * prep + .16 * hit
    neck = -.03 - .18 * prep + .24 * hit
    yaw = side * (.15 * prep - .09 * hit)
    shift = Vector((side * (.013 * hipprep - .009 * hiphit),
                    .040 * hipprep - .045 * hiphit,
                    .0015 * math.sin(phase) - .025 * hipprep - .035 * hiphit))
    rotate('Root', (1, 0, 0), pitch)
    rotate('Root', (0, 1, 0), side * (-.045 * hipprep + .03 * hiphit))
    rig.pose.bones['Root'].location = axes['Root'] @ shift
    for i, amount in [(1, .55), (2, .45)]:
        rotate('Spine' + str(i), (1, 0, 0), spine * amount)
        rotate('Spine' + str(i), (0, 0, 1), yaw * .2)
    for i in range(1, 4):
        rotate('Neck' + str(i), (1, 0, 0), neck / 3)
        rotate('Neck' + str(i), (0, 0, 1), yaw / 3)
    rotate('Head', (1, 0, 0), -neck * .25 - .40 * hit)
    rotate('Jaw', (1, 0, 0), -.08 + .03 * prep + (.38 if name == 'Cast' else .30) * hit)
    for i in range(1, 9):
        rotate('Tail' + str(i), (0, 0, 1),
               (.012 + .004 * i) * math.sin(phase - i * .4) - side * .018 * hipprep)
        rotate('Tail' + str(i), (1, 0, 0),
               (.04 - pitch) if i == 1 else .006 * math.sin(phase - i * .5))
    for side_name, sign in [('L', 1), ('R', -1)]:
        rotate(side_name + 'UpperArm', (1, 0, 0), -.18 * prep - .36 * hit)
        rotate(side_name + 'ForeArm', (1, 0, 0), .03 * math.sin(phase - .6) - .06 * prep + .08 * hit)
        rotate(side_name + 'Hand', (1, 0, 0), -.03 * math.sin(phase))
    bpy.context.view_layer.update()
    for side_name, sign in [('L', 1), ('R', -1)]:
        hip = rig.pose.bones[side_name + 'Thigh'].head.copy()
        posing.two_bone_ik(rig, side_name + 'Thigh', side_name + 'Shin',
                           feet[side_name], hip + Vector((sign * .025, -.4, 0)))
        foot = rig.pose.bones[side_name + 'Foot']
        foot.matrix = Matrix.LocRotScale(foot.head.copy(), footq[side_name], Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    low = float(vertices()[:, 2].min())
    if low < 0:
        rig.pose.bones['Root'].location += axes['Root'] @ Vector((0, 0, -low))
    bpy.context.view_layer.update()
    co = vertices()
    return {'time': t, 'min_z': float(co[:, 2].min()), 'max_z': float(co[:, 2].max()),
            'head': list(rig.pose.bones['Head'].head), 'hip': list(rig.pose.bones['Root'].head),
            'max_foot_drift': max((rig.pose.bones[s + 'Foot'].head - feet[s]).length for s in feet)}


report = {'revision': 'v2', 'clips': {}, 'preserved_actions': preserved}
for name in ('Attack', 'Cast'):
    bpy.data.actions.remove(bpy.data.actions[name])
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data.action = action
    samples = []
    for frame in range(28):
        samples.append(pose(name, frame / 24))
        for bone in rig.pose.bones:
            for prop in ('location', 'rotation_quaternion', 'scale'):
                bone.keyframe_insert(prop, frame=frame)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    assert tuple(action.frame_range) == (0, 27)
    assert all(s['min_z'] > -.001 and s['max_foot_drift'] < .006 for s in samples), samples
    assert all(np.isfinite(s['head']).all() for s in samples)
    report['clips'][name] = {'duration': 1.125, 'release': .75, 'frames': 27, 'samples': samples}
assert preserved == {a.name: action_hash(a) for a in bpy.data.actions if a.name not in ('Attack', 'Cast')}
rig.animation_data.action = bpy.data.actions['Standing']
scene.frame_set(0)
for obj in bpy.data.objects:
    obj.select_set(obj in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'export/mm6_drag.blend'))
bpy.ops.export_scene.gltf(filepath=str(P / 'export/mm6_drag_selected.glb'), use_selection=True,
    export_format='GLB', export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
    export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
    export_attributes=False, export_morph=False, export_image_format='AUTO',
    export_reset_pose_bones=True, export_anim_slide_to_zero=True)
(P / 'review/motion_v2.json').write_text(json.dumps(report, indent=2))
print('MOTION V2 PASS: two 27-frame clips; planted feet; seven original actions unchanged')
