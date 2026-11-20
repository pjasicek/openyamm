"""Retarget a Meshy auto-rig clip (24 bones) onto the MPFB Mixamo rig by world-space rest deltas.

Args: source_glb action_name out_blend [arm_swing_scale]. Opens work/rigged_v1.blend (or out_blend if it exists)
and stores/overwrites the named action on Peasant_Rig. Root forward drift is removed (in-place gait).
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, posing as P

args = sys.argv[sys.argv.index('--') + 1:]
source, action_name, out_blend = args[0], args[1], args[2]
arm_swing = float(args[3]) if len(args) > 3 else 1.0
start = out_blend if os.path.exists(out_blend) else os.path.join(common.WORK, 'rigged_v1.blend')
bpy.ops.wm.open_mainfile(filepath=start)
rig = bpy.data.objects['Peasant_Rig']
before = set(bpy.data.objects)
before_actions = set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=source)
imported = [o for o in bpy.data.objects if o not in before]
src = next(o for o in imported if o.type == 'ARMATURE')
src_action = src.animation_data.action
if os.environ.get('SRC_ACTION'):                      # multi-clip GLB: pick the clip by (partial) name
    want = os.environ['SRC_ACTION'].lower()
    src_action = next(a for a in bpy.data.actions if want in a.name.lower() and a not in before_actions)
    src.animation_data.action = src_action
f0, f1 = (int(round(x)) for x in src_action.frame_range)
MAP = {'Hips': 'Hips', 'Spine02': 'Spine', 'Spine01': 'Spine1', 'Spine': 'Spine2', 'neck': 'Neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b
order = [b.name for b in rig.data.bones if b.name.startswith('mixamorig:')]  # parents precede children


def rot_of(m):
    return m.to_3x3().normalized().to_quaternion()


src_rest = {s: rot_of(src.matrix_world @ src.data.bones[s].matrix_local) for s in MAP}
tgt_rest = {t: rot_of(rig.matrix_world @ rig.data.bones['mixamorig:' + t].matrix_local) for t in MAP.values()}
src_hips_rest = src.matrix_world @ src.data.bones['Hips'].head_local
tgt_hips_rest = rig.matrix_world @ rig.data.bones['mixamorig:Hips'].head_local
ratio = tgt_hips_rest.z / src_hips_rest.z

# Limbs are aimed joint-to-joint (rest poses differ: MakeHuman forearms point ~40 deg forward).
AIM = {}
for side in ('Left', 'Right'):
    AIM.update({side + 'Arm': (side + 'Arm', side + 'ForeArm'), side + 'ForeArm': (side + 'ForeArm', side + 'Hand'),
                side + 'UpLeg': (side + 'UpLeg', side + 'Leg'), side + 'Leg': (side + 'Leg', side + 'Foot'),
                side + 'Foot': (side + 'Foot', side + 'ToeBase')})
frames = list(range(f0, f1 + 1))
samples = []
for f in frames:
    bpy.context.scene.frame_set(f)
    rots = {s: rot_of(src.matrix_world @ src.pose.bones[s].matrix) for s in MAP}
    hips = src.matrix_world @ src.pose.bones['Hips'].head
    dirs = {t: ((src.matrix_world @ src.pose.bones[c].head) - (src.matrix_world @ src.pose.bones[a].head)).normalized()
            for t, (a, c) in AIM.items()}
    samples.append((rots, hips, dirs))
hips_d = np.array([tuple((h - src_hips_rest) * ratio) for _, h, _ in samples])
t = np.arange(len(frames))
for axis in (0, 1):  # remove travel and any linear drift; keep sway/bob
    slope, intercept = np.polyfit(t, hips_d[:, axis], 1)
    hips_d[:, axis] -= slope * t + intercept

if rig.animation_data is None:
    rig.animation_data_create()
old = bpy.data.actions.get(action_name)
if old:
    bpy.data.actions.remove(old)
action = bpy.data.actions.new(action_name)
action.use_fake_user = True
rig.animation_data.action = action
for i, (f, (rots, _, dirs)) in enumerate(zip(frames, samples)):
    rig.animation_data.action = None        # an attached action would re-evaluate over the pose being built
    P.reset(rig)
    for name in order:
        short = name[10:]
        src_name = next((s for s, tname in MAP.items() if tname == short), None)
        if src_name is None:
            continue
        if short in AIM:
            child = 'mixamorig:' + AIM[short][1]
            bone = rig.pose.bones[name]
            current = rig.pose.bones[child].head - bone.head
            desired = rig.matrix_world.to_quaternion().inverted() @ dirs[short]
            if short.endswith(('Arm', 'ForeArm')) and arm_swing != 1.0:
                rest_dir = (rig.data.bones[child].head_local - rig.data.bones[name].head_local).normalized()
                desired = rest_dir.lerp(desired, arm_swing).normalized() if short.endswith('Arm') else desired
            q = current.normalized().rotation_difference(desired)
            head = bone.head.copy()
            bone.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ bone.matrix
            bpy.context.view_layer.update()
            continue
        delta = rots[src_name] @ src_rest[src_name].inverted()
        if short in ('LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm') and arm_swing != 1.0:
            delta = Quaternion().slerp(delta, arm_swing)
        world = delta @ tgt_rest[short]
        bone = rig.pose.bones[name]
        head = bone.head.copy()
        if short == 'Hips':
            head = rig.matrix_world.inverted() @ (tgt_hips_rest + Vector(hips_d[i]))
        bone.matrix = Matrix.LocRotScale(head, (rig.matrix_world.to_quaternion().inverted() @ world), Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    P.curl_hand(rig, 'Left', 14, thumb=6)
    P.curl_hand(rig, 'Right', float(os.environ.get('RIGHT_CURL', 14)), thumb=float(os.environ.get('RIGHT_THUMB', 6)))
    frame = f - f0 + 1
    rig.animation_data.action = action
    for bone in rig.pose.bones:
        bone.keyframe_insert('rotation_quaternion', frame=frame)
        if bone.name == 'mixamorig:Hips':
            bone.keyframe_insert('location', frame=frame)
action['source'] = os.path.basename(source)
action['frames'] = len(frames)
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)
print('RETARGETED', action_name, len(frames), 'frames', 'ratio', round(ratio, 3))
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
