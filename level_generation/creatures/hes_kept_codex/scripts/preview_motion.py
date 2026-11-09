"""Kept G1: source mannequin, fitted handle axis, real prop dimensions and CPU review renders.
The grip circle/axis fit follows mm6_natm_claude/scripts/grip_from_source.py.
No source library files or other creature projects are written.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--library', choices=['1Hand', 'Unarmed', 'Relax', 'Armed', 'Mixamo'], required=True)
parser.add_argument('--prop', choices=['club', 'pick', 'none'], default='none')
parser.add_argument('--clips', nargs='+', required=True)
parser.add_argument('--frames', type=int, default=5)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source = REPO / 'anim_library/humanoid_set' / (args.library + '.glb')
if args.library == 'Mixamo':
    source = REPO / 'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'
    assert args.prop == 'none'
out = ROOT / 'review/g1' / args.prop
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
if args.library == 'Mixamo':
    bpy.ops.import_scene.fbx(filepath=str(source))
else:
    bpy.ops.import_scene.gltf(filepath=str(source))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mixamo_actions = {}
if args.library == 'Mixamo':
    for clip in args.clips:
        before, old_actions = set(bpy.data.objects), set(bpy.data.actions)
        clip_path = REPO / 'anim_library/mixamo' / (clip + '.fbx')
        bpy.ops.import_scene.fbx(filepath=str(clip_path))
        new = set(bpy.data.objects) - before
        source_arm = next(o for o in new if o.type == 'ARMATURE')
        assert set(b.name for b in source_arm.data.bones) <= set(b.name for b in arm.data.bones)
        action = next(iter(set(bpy.data.actions) - old_actions))
        action.use_fake_user = True
        mixamo_actions[clip] = action
        for obj in new:
            bpy.data.objects.remove(obj, do_unlink=True)
    assert scene.render.fps == 30
arm.animation_data.action = None
for track in arm.animation_data.nla_tracks:
    track.mute = True
for bone in arm.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
arm.rotation_mode = 'XYZ'
if args.library == 'Mixamo':
    prefix = next(b.name for b in arm.data.bones if b.name.endswith('Hips'))[:-4]
    direction = sum((arm.matrix_world.to_3x3() @
                     (arm.data.bones[prefix + side + 'ToeBase'].head_local -
                      arm.data.bones[prefix + side + 'Foot'].head_local)
                     for side in ('Left', 'Right')), Vector())
    arm.rotation_euler.z += -math.pi / 2 - math.atan2(direction.y, direction.x)
else:
    arm.rotation_euler = (0, 0, math.pi)
bpy.context.view_layer.update()
body = [o for o in bpy.data.objects if o.type == 'MESH' and
        (o.parent is arm or any(m.type == 'ARMATURE' and m.object is arm for m in o.modifiers))]
assert body, 'Source mannequin absent'
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj not in body:
        obj.hide_render = True
points = [o.matrix_world @ v.co for o in body for v in o.data.vertices]
zmin, zmax = min(p.z for p in points), max(p.z for p in points)
assert 1 < zmax - zmin < 4, (zmin, zmax)
source_height = zmax - zmin
arm.scale *= 1.7 / source_height
bpy.context.view_layer.update()
points = [o.matrix_world @ v.co for o in body for v in o.data.vertices]
arm.location.z -= min(p.z for p in points)
bpy.context.view_layer.update()
actions = {a.name.split('@')[-1].split('|')[-1]: a for a in bpy.data.actions}
actions.update(mixamo_actions)


def activate(name):
    act = actions[name]
    arm.animation_data.action = act
    if act.slots:
        arm.animation_data.action_slot = act.slots[0]
    return act


def bone_name(name):
    if args.library != 'Mixamo':
        return name
    trunk = {'B_Spine':'Spine', 'B_Spine1':'Spine1', 'B_Spine2':'Spine2', 'B_Neck':'Neck', 'B_Head':'Head'}
    if name in trunk:
        return prefix + trunk[name]
    _, side, part = name.split('_')
    part = {'Clavicle':'Shoulder', 'UpperArm':'Arm', 'Forearm':'ForeArm', 'Hand':'Hand',
            'Finger2':'HandMiddle1', 'Thigh':'UpLeg', 'Calf':'Leg', 'Foot':'Foot'}[part]
    return prefix + {'L':'Left', 'R':'Right'}[side] + part


def point(name):
    return arm.matrix_world @ arm.pose.bones[bone_name(name)].head


# Segment axes and swing/twist follow the playbook's rom_extract.py; imported tails are unusable.
joints = {'B_Spine':'B_Spine1', 'B_Spine1':'B_Spine2', 'B_Spine2':'B_Neck', 'B_Neck':'B_Head'}
for side in ('L', 'R'):
    for parent, child in [('Clavicle','UpperArm'), ('UpperArm','Forearm'), ('Forearm','Hand'),
                          ('Hand','Finger2'), ('Thigh','Calf'), ('Calf','Foot')]:
        joints[f'B_{side}_{parent}'] = f'B_{side}_{child}'
axes = {}
for parent, child in joints.items():
    b, c = arm.data.bones[bone_name(parent)], arm.data.bones[bone_name(child)]
    axes[parent] = (b.matrix_local.to_3x3().inverted() @ (c.head_local-b.head_local)).normalized()


def joint_angles():
    values = {}
    for name, axis in axes.items():
        q = arm.pose.bones[bone_name(name)].matrix_basis.to_quaternion().normalized()
        twist = 2 * math.atan2(Vector((q.x,q.y,q.z)).dot(axis), q.w)
        twist = (twist + math.pi) % (2*math.pi) - math.pi
        values[name + '_swing'] = math.degrees(axis.angle(q @ axis))
        values[name + '_twist'] = math.degrees(twist)
    for side in ('L','R'):
        shoulder, elbow, wrist, finger = [point(f'B_{side}_{part}')
                                         for part in ('UpperArm','Forearm','Hand','Finger2')]
        values[side + '_elbow_flex'] = math.degrees((elbow-shoulder).angle(wrist-elbow))
        values[side + '_wrist_bend'] = math.degrees((wrist-elbow).angle(finger-wrist))
    assert all(math.isfinite(value) for value in values.values())
    return values


def circle(points):
    centre = points.mean(0)
    _, _, vt = np.linalg.svd(points - centre)
    xy = (points - centre) @ vt[:2].T
    solution = np.linalg.lstsq(np.column_stack([2 * xy, np.ones(3)]),
                             (xy * xy).sum(1), rcond=None)[0]
    assert np.isfinite(solution).all()
    return centre + solution[:2] @ vt[:2]


activate(args.clips[0])
scene.frame_set(0)
grip = None
prop_objects = []
prop_local = {}
if args.prop != 'none':
    centres = []
    for finger in range(1, 5):
        names = [f'B_R_Finger{finger}', f'B_R_Finger{finger}1', f'B_R_Finger{finger}2']
        centres.append(circle(np.array([point(n) for n in names])))
    centres = np.array(centres)
    centre = centres.mean(0)
    axis = np.linalg.svd(centres - centre)[2][0]
    if np.dot(np.array(point('B_R_Finger1') - point('B_R_Finger4')), axis) < 0:
        axis = -axis
    hand = arm.matrix_world @ arm.pose.bones['B_R_Hand'].matrix
    inv = hand.inverted()
    grip_centre = inv @ Vector(centre)
    grip_axis = (inv.to_3x3() @ Vector(axis)).normalized()
    finger_axis = (inv.to_3x3() @ (point('B_R_Finger2') - point('B_R_Hand'))).normalized()
    fit_error = np.linalg.norm((centres-centre) - np.outer((centres-centre) @ axis, axis), axis=1)
    assert fit_error.max() < 0.02, fit_error
    grip = {'centre_hand': list(grip_centre), 'axis_hand': list(grip_axis),
            'finger_axis_hand': list(finger_axis), 'circle_centres_line_error_m': float(fit_error.max())}
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / 'work/props' / ('hes_kept_' + args.prop + '.glb')))
    prop_objects = [o for o in set(bpy.data.objects)-before if o.type == 'MESH']
    assert prop_objects
    for obj in prop_objects:
        prop_local[obj.name] = obj.matrix_world.copy()
        obj.parent = None


def prop_frame():
    hand = arm.matrix_world @ arm.pose.bones['B_R_Hand'].matrix
    centre = hand @ grip_centre
    zaxis = (hand.to_3x3() @ grip_axis).normalized()
    xaxis = hand.to_3x3() @ finger_axis
    xaxis = (xaxis - zaxis * xaxis.dot(zaxis)).normalized()
    yaxis = zaxis.cross(xaxis).normalized()
    rotation = Matrix((xaxis, yaxis, zaxis)).transposed()
    assert abs(rotation.determinant() - 1) < 1e-5
    frame = rotation.to_4x4()
    frame.translation = centre
    for obj in prop_objects:
        obj.matrix_world = frame @ prop_local[obj.name]
    return frame


clay = bpy.data.materials.new('SourceMannequinClay')
clay.diffuse_color = (0.42, 0.46, 0.5, 1)
clay.use_nodes = True
bsdf = clay.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = clay.diffuse_color
bsdf.inputs['Roughness'].default_value = 0.85
for obj in body:
    obj.data.materials.clear()
    obj.data.materials.append(clay)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = 320
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('ReviewWorld')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.28, 0.28, 0.28, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.7
for location, power in [((3, -4, 5), 500), ((-3, -1, 3), 350)]:
    data = bpy.data.lights.new('softbox', 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = 4
    light = bpy.data.objects.new('softbox', data)
    scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector((0, 0, 0.9)) - light.location).to_track_quat('-Z', 'Y').to_euler()
cam_data = bpy.data.cameras.new('MotionReview')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 3.1
cam = bpy.data.objects.new('MotionReview', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
for clip in args.clips:
    act = activate(clip)
    first, last = act.frame_range
    assert last > first
    samples = []
    for frame in np.arange(first, last + 0.01, 0.5):
        scene.frame_set(int(frame), subframe=float(frame % 1))
        transform = prop_frame() if grip else None
        wrist = point('B_R_Hand')
        knuckle = point('B_R_Finger2')
        if args.prop == 'pick':
            tips = [transform @ Vector((x, 0, 0.43)) for x in (-0.23, 0.2)]
        elif args.prop == 'club':
            tips = [transform @ Vector((0, 0, 0.48))]
        else:
            tips = [knuckle]
        samples.append({'frame':float(frame), 'time_s':float((frame-first)/30),
                        'hand':list(wrist), 'strike_points':[list(t) for t in tips],
                        'joint_angles_degrees':joint_angles(),
                        'ankles':{side:list(point(f'B_{side}_Foot')) for side in ('L','R')}})
    tips = np.array([s['strike_points'] for s in samples])
    assert np.isfinite(tips).all()
    extent = np.ptp(tips.reshape(-1, 3), axis=0)
    assert extent.max() > 0.001, 'No source motion sampled'
    forward = -tips[:, :, 1]
    at = np.unravel_index(forward.argmax(), forward.shape)
    report = {'source':str(source.relative_to(REPO)), 'source_sha256':source_hash, 'clip':clip,
              'prop':args.prop, 'source_rest_height_m':source_height, 'review_height_m':1.7,
              'fps':30, 'duration_s':float((last-first)/30), 'grip':grip,
              'forward_axis':'Blender -Y', 'samples':samples,
              'maximum_forward_m':float(forward.max()), 'maximum_forward_sample':int(at[0]),
              'maximum_forward_tip':int(at[1]), 'height_at_maximum_forward_m':float(tips[at][2]),
              'strike_point_height_range_m':[float(tips[:,:,2].min()),float(tips[:,:,2].max())],
              'gate_scope':'source motion/prop selection only; not final Kept rig or collision clearance'}
    rom = {}
    stress_frames = set()
    for metric in samples[0]['joint_angles_degrees']:
        values = np.array([sample['joint_angles_degrees'][metric] for sample in samples])
        lo, hi = int(values.argmin()), int(values.argmax())
        rom[metric] = {'min':float(values[lo]), 'max':float(values[hi]),
                       'min_frame':samples[lo]['frame'], 'max_frame':samples[hi]['frame']}
        stress_frames.update((samples[lo]['frame'], samples[hi]['frame']))
    report['rom_degrees'] = rom
    report['stress_frames'] = sorted(stress_frames)
    if args.library == 'Mixamo':
        clip_path = REPO / 'anim_library/mixamo' / (clip + '.fbx')
        report['motion_source'] = str(clip_path.relative_to(REPO))
        report['motion_sha256'] = hashlib.sha256(clip_path.read_bytes()).hexdigest()
    (out/(clip+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    image_rows = []
    render_frames = list(np.linspace(first,last,args.frames))
    if 'Attack' in clip:
        travel = forward.max(axis=1)
        impact_index = int(np.flatnonzero(travel >= travel[0] + 0.95*(travel.max()-travel[0]))[0])
        report['forward95_probe'] = {'frame':samples[impact_index]['frame'],
                                     'time_s':samples[impact_index]['time_s'],
                                     'strike_points':samples[impact_index]['strike_points']}
        render_frames = sorted(set(render_frames + [samples[impact_index]['frame'],samples[at[0]]['frame']]))
        (out/(clip+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    for view, location in [('front',(0,-5,1.15)), ('side',(5,0,1.15)), ('quarter',(3,-4,1.15))]:
        cam.location = location
        cam.rotation_euler = (Vector((0,-0.35,0.95))-cam.location).to_track_quat('-Z','Y').to_euler()
        row = []
        for i, frame in enumerate(render_frames):
            scene.frame_set(int(frame),subframe=float(frame%1))
            if grip:
                prop_frame()
            target = out/f'{clip}_{view}_{i}.png'
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
            row.append({'path':str(target.relative_to(ROOT)), 'frame':float(frame)})
        image_rows.append({'view':view,'frames':row})
    (out/(clip+'_frames.json')).write_text(json.dumps(image_rows,indent=2)+'\n')
    print('G1_DONE',args.prop,clip,'duration',report['duration_s'],'max reach',report['maximum_forward_m'],
          'height',report['height_at_maximum_forward_m'],flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)

