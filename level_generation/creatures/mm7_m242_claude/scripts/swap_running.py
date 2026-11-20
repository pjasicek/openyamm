"""Running-only fit from the project's Mixamo retarget/twist output; no mesh or rig edits.
Run from the project: blender -b --threads 4 --python scripts/swap_running.py.
"""
import bpy
import hashlib
import json
import math
import os
import sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
base, donor, output = args or ['work/pre_runswap3_20261013/work/rig_v5.blend',
                               'work/run2_twist.blend', 'work/run3_fitted.blend']
bpy.ops.wm.open_mainfile(filepath=str(ROOT / base))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene

def curves(action):
    return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]

def digest(action):
    data = [(fc.data_path, fc.array_index, [(list(k.co), list(k.handle_left), list(k.handle_right),
             k.interpolation) for k in fc.keyframe_points]) for fc in curves(action)]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

before = {a.name: digest(a) for a in bpy.data.actions if a.name != 'Running'}
bpy.data.actions.remove(bpy.data.actions['Running'])
with bpy.data.libraries.load(str(ROOT / donor), link=False) as (_, target):
    target.actions = ['Running']
source = target.actions[0]
rig.animation_data_create()
def set_action(action):
    rig.animation_data.action = action
    if action and action.slots:
        rig.animation_data.action_slot = action.slots[0]

def wm(name):
    return rig.matrix_world @ rig.pose.bones[name].matrix

def apply(pose):
    for name, (q, loc) in pose.items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = q
        pb.location = loc
    bpy.context.view_layer.update()

def aim(name, direction):
    mat = wm(name)
    current = (mat.to_3x3() @ Vector((0, 1, 0))).normalized()
    turn = current.rotation_difference(direction.normalized()).to_matrix().to_4x4()
    pos = mat.translation.copy()
    mat = turn @ mat
    mat.translation = pos
    rig.pose.bones[name].matrix = rig.matrix_world.inverted() @ mat
    bpy.context.view_layer.update()

# Read the original FBX hip profile, before the retargeter's floor correction.
set_action(bpy.data.actions['Standing'])
scene.frame_set(0)
standing_height = wm('B_Pelvis').translation.z
objects_before = set(bpy.data.objects)
actions_before = set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=str(ROOT.parents[2] / 'anim_library/mixamo/Standard Run.fbx'))
src = next(o for o in set(bpy.data.objects)-objects_before if o.type == 'ARMATURE')
prefix = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
start, end = src.animation_data.action.frame_range
source_z = []
for f in range(int(start), int(end)):
    scene.frame_set(f)
    source_z.append((src.matrix_world @ src.pose.bones[prefix+'Hips'].head).z)
for obj in set(bpy.data.objects)-objects_before:
    bpy.data.objects.remove(obj, do_unlink=True)
for action in set(bpy.data.actions)-actions_before:
    bpy.data.actions.remove(action)
# Preserve the source timing/shape, remove left/right bob asymmetry and soften key noise.
bob = np.array(source_z)
bob = (bob + np.roll(bob, len(bob)//2)) / 2
bob = (np.roll(bob, 1) + 2*bob + np.roll(bob, -1)) / 4
bob = (bob-bob.min()) * 1.065446897 * 0.45
pelvis_height = standing_height * 0.921 + bob
assert min(pelvis_height) >= 0.92 * standing_height

set_action(bpy.data.actions['Walking'])
scene.frame_set(6)
hand_pose = {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones
             if pb.name == 'B_R_Hand' or pb.name.startswith('B_L_Finger')}

# Standard Run is one 22-frame cycle. Close the source rotations continuously;
# the final key is copied exactly from the first.
SUBSTEPS = 4
N = 22 * SUBSTEPS
set_action(source)
poses = []
for f in range(N + 1):
    scene.frame_set(f // SUBSTEPS, subframe=(f % SUBSTEPS) / SUBSTEPS)
    poses.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones})
for f, pose in enumerate(poses):
    t = f / N
    for name, (q, loc) in list(pose.items()):
        q0, l0 = poses[0][name]
        q1, l1 = poses[-1][name]
        correction = q1.rotation_difference(q0)
        pose[name] = (q @ Quaternion().slerp(correction, t), loc.lerp(loc + l0 - l1, t))
set_action(None)
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest_pelvis = wm('B_Pelvis').translation.copy()
feet = {}
for side in 'LR':
    foot = wm(f'B_{side}_Foot')
    body = bpy.data.objects['Body']
    ids = {g.index for g in body.vertex_groups if g.name.startswith(f'B_{side}_Foot')
           or g.name.startswith(f'B_{side}_Toe')}
    points = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices
                       if sum(g.weight for g in v.groups if g.group in ids) > 0.3])
    points = points[points[:,2] <= points[:,2].min()+0.005]
    along = -points[:,1]
    toe = Vector(points[along >= np.quantile(along,.7)].mean(0)-
                 points[along <= np.quantile(along,.3)].mean(0))
    yaw = math.atan2(toe.x, -toe.y)
    rot = Matrix.Rotation(-yaw, 3, 'Z') @ foot.to_3x3()
    feet[side] = (foot.translation.copy(), rot)
grip = json.loads((ROOT / 'work/grip_pose.json').read_text())
G = grip['finger_local']
stride = 1.6
stance = 0.35
fitted = []
for f, pose in enumerate(poses[:-1]):
    apply(pose)
    mat = wm('B_Pelvis')
    mat.translation.x = rest_pelvis.x + 0.012 * math.sin(2 * math.pi * f / N)
    mat.translation.y = rest_pelvis.y
    mat.translation.z = float(np.interp(f/SUBSTEPS, np.arange(23), np.r_[pelvis_height, pelvis_height[0]]))
    rig.pose.bones['B_Pelvis'].matrix = rig.matrix_world.inverted() @ mat
    bpy.context.view_layer.update()
    for side, offset in [('L', -0.25), ('R', 0.25)]:
        phase = (f / N + offset) % 1.0
        home, rotation = feet[side]
        pitch = 0.0
        if phase < stance:
            y = stride * (phase - stance/2)
            lift = 0.0
        else:
            t = (phase - stance) / (1-stance)
            # Hermite return: match the stance velocity at both contacts.
            y = stride * (stance/2 + (1-stance)*t - 3*t*t + 2*t*t*t)
            lift = 0.25 * math.sin(math.pi*t) ** 1.5
            pitch = math.radians(38) * math.sin(math.pi*t) ** 2
        target = Vector((home.x, 0.040 + y, home.z + 0.007 + lift))
        th, ca, ft = (f'B_{side}_{part}' for part in ('Thigh', 'Calf', 'Foot'))
        hip, knee, ankle = (wm(n).translation for n in (th, ca, ft))
        a, b = (knee-hip).length, (ankle-knee).length
        d = (target-hip).length
        assert d < a+b, (f, side, d, a+b)
        u = (target-hip).normalized()
        forward = Vector((0,-1,0))
        v = (forward-u*forward.dot(u)).normalized()
        c = (a*a+d*d-b*b)/(2*a*d)
        kn = hip+a*(u*c+v*math.sqrt(max(0,1-c*c)))
        aim(th, kn-hip)
        aim(ca, target-wm(ca).translation)
        mat = (Matrix.Rotation(pitch, 3, 'X') @ rotation).to_4x4(); mat.translation = wm(ft).translation
        rig.pose.bones[ft].matrix = rig.matrix_world.inverted() @ mat
        rig.pose.bones[f'B_{side}_Toe0'].matrix_basis.identity()
        bpy.context.view_layer.update()
    # Keep Standard Run's twist/sway but bring the trunk to a slight forward lean.
    delta = wm('B_Neck').translation - wm('B_Spine').translation
    lean = math.atan2(-delta.y, delta.z)
    mat = wm('B_Spine'); pos = mat.translation.copy()
    mat = Matrix.Rotation(math.radians(16) - lean, 4, 'X') @ mat
    mat.translation = pos
    rig.pose.bones['B_Spine'].matrix = rig.matrix_world.inverted() @ mat
    bpy.context.view_layer.update()
    # Keep the calibrated carrying wrist and open left fingers; the source's unarmed wrist
    # folds the blade back into the head and its foreign finger curl tears the left web.
    for side, sign in [('R', 1), ('L', -1)]:
        name = f'B_{side}_UpperArm'
        mat = wm(name); pos = mat.translation.copy()
        mat = Matrix.Rotation(sign * math.radians(9), 4, 'Y') @ mat
        mat.translation = pos
        rig.pose.bones[name].matrix = rig.matrix_world.inverted() @ mat
        bpy.context.view_layer.update()
    for name, q in hand_pose.items():
        rig.pose.bones[name].rotation_quaternion = Quaternion() if name.startswith('B_L_Finger') else q
    bpy.context.view_layer.update()
    for side in 'LR':
        upper, fore, hand = (f'B_{side}_{n}' for n in ('UpperArm', 'Forearm', 'Hand'))
        hand_rotation = wm(hand).to_3x3()
        hinge = (wm(upper).to_3x3() @ Vector((0, 0, -1))).normalized()
        direction = wm(hand).translation - wm(fore).translation
        direction -= hinge * direction.dot(hinge)
        aim(fore, direction)
        # Resolve the elbow in its hinge plane while preserving the carried blade direction.
        mat = hand_rotation.to_4x4(); mat.translation = wm(hand).translation
        rig.pose.bones[hand].matrix = rig.matrix_world.inverted() @ mat
        bpy.context.view_layer.update()
    # Supinate the sword forearm for a vertical running carry; keep the wrist/grip fixed.
    fore = wm('B_R_Forearm'); pos = fore.translation.copy()
    axis = (wm('B_R_Hand').translation - pos).normalized()
    fore = Matrix.Rotation(math.radians(70), 4, axis) @ fore
    fore.translation = pos
    rig.pose.bones['B_R_Forearm'].matrix = rig.matrix_world.inverted() @ fore
    bpy.context.view_layer.update()
    for name, q in G.items():
        rig.pose.bones[name].rotation_quaternion = Quaternion(q)
    bpy.context.view_layer.update()
    # The project's twist_bones.py calibration, applied only to this action.
    for side in 'LR':
        fb, hb = (rig.data.bones[f'B_{side}_{n}'] for n in ('Forearm','Hand'))
        axis = (fb.matrix_local.inverted() @ hb.head_local).normalized()
        rel = (wm(fb.name).inverted() @ wm(hb.name)).to_quaternion()
        rest = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
        q = rel @ rest.inverted()
        tw = (2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
        rig.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion = Quaternion(axis, 0.6*tw)
    bpy.context.view_layer.update()
    fitted.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones})
fitted.append(fitted[0])
bpy.data.actions.remove(source)
action = bpy.data.actions.new('Running'); action.use_fake_user = True
set_action(action)
for f, pose in enumerate(fitted):
    apply(pose)
    for pb in rig.pose.bones:
        if f % SUBSTEPS and pb.name != 'B_Pelvis' and not any(k in pb.name for k in ('Thigh', 'Calf', 'Foot', 'Toe')):
            continue
        pb.keyframe_insert('rotation_quaternion', frame=f/SUBSTEPS)
        if pb.name == 'B_Pelvis':
            pb.keyframe_insert('location', frame=f/SUBSTEPS)
for fc in curves(action):
    for key in fc.keyframe_points:
        key.interpolation = 'LINEAR'
action.use_frame_range = True; action.frame_start = 0; action.frame_end = N/SUBSTEPS
action['export_substeps'] = SUBSTEPS
set_action(None)
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
assert before == {a.name: digest(a) for a in bpy.data.actions if a.name != 'Running'}
scene.render.fps = 30
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / output))
print('RUN_FIT', {'frames': N+1, 'stride_m': stride, 'stance_fraction': stance, 'pelvis_min_pct': min(pelvis_height)/standing_height*100, 'pelvis_mean_pct': float(pelvis_height.mean())/standing_height*100, 'unchanged_actions': before})
