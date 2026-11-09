"""Adapt local upper-body motion onto the seated rest pose; author the acid-spit lean."""
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
pilot = 'pilot' in sys.argv
sys.path.insert(0, str(P / 'scripts'))
from arm_contact import pin_arm
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_v2.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
FPS = 30
MAP = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2',
       'B_Neck': 'Neck', 'B_Head': 'Head'}
for side, full in (('L', 'Left'), ('R', 'Right')):
    for ours, theirs in (('Clavicle', 'Shoulder'), ('UpperArm', 'Arm'), ('Forearm', 'ForeArm'), ('Hand', 'Hand')):
        MAP[f'B_{side}_{ours}'] = full + theirs
    for digit, name in enumerate(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
        chain = [f'B_{side}_Finger{digit}', f'B_{side}_Finger{digit}1', f'B_{side}_Finger{digit}2']
        if side == 'R' and digit == 0:
            chain = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
        for k, bone in enumerate(chain):
            MAP[bone] = f'{full}Hand{name}{k + 1}'
REST = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
names = [b.name for b in rig.data.bones if b.name in MAP and b.name != 'B_Pelvis']
report = {}
WRISTS = {s: rig.data.bones[f'B_{s}_Hand'].head_local.copy() for s in 'LR'}
def plant_hands():
    for side in 'LR':
        pin_arm(rig, side, WRISTS[side], REST[f'B_{side}_Hand'])
    for pb in rig.pose.bones:
        if 'Finger' in pb.name: pb.matrix_basis.identity()
    bpy.context.view_layer.update()



def use(action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if action and len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


def reset():
    use(None)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def smooth(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def write(name, frames):
    reset()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    use(action)
    last = {}
    for i, frame in enumerate(frames):
        for pb in rig.pose.bones:
            q = frame.get(pb.name, Quaternion()).copy()
            if pb.name in last and last[pb.name].dot(q) < 0:
                q.negate()
            last[pb.name] = q.copy()
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=i)
    action.use_frame_range = True
    action.frame_start, action.frame_end = 0, len(frames) - 1
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    reset()
    return action


SOURCES = {'Standing': 'Breathing Idle', 'Fidget': 'Look Around',
           'Hit': 'Standing React Large From Front'}
for role, source_name in SOURCES.items():
    if pilot and role != 'Standing':
        continue
    path = REPO / 'anim_library/mixamo' / (source_name + '.fbx')
    before, acts_before = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(path))
    new = set(bpy.data.objects) - before
    source = next(o for o in new if o.type == 'ARMATURE')
    source_action = source.animation_data.action
    source_fps = scene.render.fps / scene.render.fps_base
    prefix = next(b.name for b in source.data.bones if b.name.endswith('Hips'))[:-4]
    first, last = source_action.frame_range
    duration = (last - first) / source_fps
    count = int(round(duration * FPS))
    scene.frame_set(int(first), subframe=first - int(first))
    initial = {n: (source.matrix_world @ source.pose.bones[prefix + MAP[n]].matrix).to_quaternion()
               for n in names}
    align = {n: REST[n] @ initial[n].inverted() for n in names}
    frames = []
    for i in range(count + 1):
        f = first + (i / FPS) * source_fps
        scene.frame_set(int(f), subframe=f - int(f))
        reset()
        for n in names:
            if 'Finger' in n:
                gain = 0.
            elif role == 'Standing':
                gain = .35 if ('Spine' in n or n in ('B_Neck', 'B_Head')) else .20
            elif role == 'Fidget':
                gain = .10 if n in ('B_Neck', 'B_Head') else 0.
            elif role == 'Hit':
                gain = .08 if ('Spine' in n or n in ('B_Neck', 'B_Head')) else 0.
            else:
                gain = .30 if 'Spine' in n else (.45 if n in ('B_Neck', 'B_Head') else .18)
            # Preserve the selected seated rest pose; apply the source's world-frame changes at its own rate.
            source_world = (source.matrix_world @ source.pose.bones[prefix + MAP[n]].matrix).to_quaternion()
            target = REST[n].slerp(align[n] @ source_world, gain)
            matrix = target.to_matrix().to_4x4()
            matrix.translation = rig.pose.bones[n].head
            rig.pose.bones[n].matrix = matrix
            bpy.context.view_layer.update()
        plant_hands()
        pose = {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones}
        # Idle loops and one-shots return to the same neutral seated pose; Death retains its final collapse.
        if role != 'Death':
            fade = 1 - smooth((i / FPS - (duration - .25)) / .25)
            pose = {n: Quaternion().slerp(q, fade) for n, q in pose.items()}
        frames.append(pose)
    for ob in new:
        bpy.data.objects.remove(ob, do_unlink=True)
    for action in set(bpy.data.actions) - acts_before:
        bpy.data.actions.remove(action)
    write(role, frames)
    report[role] = {'source': str(path.relative_to(REPO)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'duration_s': count / FPS, 'source_fps': source_fps,
                    'adaptation': 'Fixed seated base; measured rest alignment of world rotations; attenuated upper-body delta.'}
    if role == 'Death':
        write('Dead', [frames[-1]] * (FPS + 1))
        report['Dead'] = {'source': 'Death final pose', 'duration_s': 1.0}


def envelope(t):
    keys = [(0, 0), (.25, -2), (.55, 1), (.75, 8), (1.0, 3), (1.5, 0)]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if t <= tb:
            return va + (vb - va) * smooth((t - ta) / (tb - ta))
    return 0


frames = []
for i in range(46):
    reset()
    amount = envelope(i / FPS)
    for name, share in (('B_Spine', .20), ('B_Spine1', .30), ('B_Spine2', .50), ('B_Neck', .15), ('B_Head', .25)):
        pb = rig.pose.bones[name]
        world = pb.matrix.to_quaternion()
        delta = Quaternion((1, 0, 0), math.radians(amount * share))
        pb.rotation_quaternion = pb.rotation_quaternion @ (world.inverted() @ delta @ world)
        bpy.context.view_layer.update()
    plant_hands()
    frames.append({pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones})
write('Attack', frames)
report['Attack'] = {'source': 'Authored acid-spit lean; library Spit Reaction was rejected as receiving spit.',
                    'duration_s': 1.5, 'intended_release_s': .75, 'release_measurement': 'pending exported mouth trajectory'}
if not pilot:
    frames = []
    for i in range(76):
        reset()
        t = i / FPS
        fall = smooth((t - .15) / 1.45)
        settle = smooth((t - 1.6) / .9)
        for name, degrees in [('B_Spine', -1.2), ('B_Spine1', -1.6), ('B_Spine2', -1.2),
                              ('B_Neck', 8.), ('B_Head', 20.)]:
            pb = rig.pose.bones[name]
            world = pb.matrix.to_quaternion()
            amount = degrees * fall - (1.5 * settle if name == 'B_Head' else 0)
            delta = Quaternion((1, 0, 0), math.radians(amount))
            pb.rotation_quaternion = pb.rotation_quaternion @ (world.inverted() @ delta @ world)
            bpy.context.view_layer.update()
        plant_hands()
        frames.append({pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones})
    write('Death', frames)
    write('Dead', [frames[-1]] * (FPS + 1))
    report['Death'] = {'source': 'Locally authored seated collapse into cradle, followed by head slump.',
        'rejected_source': 'Standing React Death Backward: whole-body fall caused crown/cradle penetration and a 31.6-degree half-frame jump.',
        'duration_s': 2.5}
    report['Dead'] = {'source': 'Death final pose', 'duration_s': 1.0}

scene.render.fps, scene.render.fps_base = FPS, 1
reset()
(P / 'work/clip_sources.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P / ('work/pilot_clips.blend' if pilot else 'work/animated_master.blend')))
print(json.dumps(report))
