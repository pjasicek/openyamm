"""Retarget Mixamo FBX clips from anim_library onto the fire elemental's figure rig (work/figure.blend, MPFB Mixamo
skeleton, A-pose rest). Run under Blender:

    blender --background work/figure.blend --python scripts/retarget.py -- <out.blend> \
        <fbx>:<Action>[:<start>:<end>][:turn][:float][:calm] ...

<start>/<end> optionally trim the source in seconds. Keys at 24 fps (native frames are 125 ms).
turn: the magic and reaction clips stand side-on in a combat stance; the whole clip is yawed so the chest faces
forward (-Y) at its first frame. float: the legs (local) hold the Floating clip's first frame, which must be
retargeted earlier in the same run or blend; the elemental never stands on its feet. calm: legs and arms turn only
part of the way from the rest pose (CALM: the sprite's figure hangs with its legs nearly straight and together, its
arms angled down inside the cage).

The library's Mixamo files are retargeted to a hunched skeleton whose rest pose is a T-pose, while ours is MPFB's
A-pose. Spine, neck, head, shoulders (clavicles) and legs copy the source's WORLD rotation change from its rest, D(t) = M(t) M_rest^-1,
applied to our own rest (the source's hunch is not copied). Arms (shoulder to hand) instead copy the source's
absolute directions: our rest bone is first turned onto the source's rest direction (A-pose to T-pose), then D(t)
is applied (aligning the clavicles too shrugged them 35 degrees up), so raised and spread arms keep their height. The source is first yawed to face -Y like our rig.
Hips: rotation as above, travel = source hips travel x the height ratio. Fingers keep their rest pose.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index('--') + 1:]
out_blend, items = os.path.abspath(args[0]), args[1:]
FPS = 24
scene = bpy.context.scene
rig = bpy.data.objects['FireElemental_Rig']
ARM_PARTS = ('Arm', 'ForeArm', 'Hand')
DELTA = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'LeftShoulder', 'RightShoulder', 'LeftUpLeg', 'LeftLeg',
         'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase']
ARMS = [side + part for side in ('Left', 'Right') for part in ARM_PARTS]
MAPPED = DELTA + ARMS
LEGS = [side + part for side in ('Left', 'Right') for part in ('UpLeg', 'Leg', 'Foot', 'ToeBase')]
# calm: share of the source's turn from our rest each bone keeps (legs hang nearly straight, arms stay near the A-pose
# so the hands stay inside the flame cage as in the sprite).
CALM = {**{n: 0.15 for n in LEGS},
        **{side + part: 0.2 for side in ('Left', 'Right') for part in ('Shoulder', 'Arm', 'ForeArm')}}
names = [b.name for b in rig.data.bones]
order = [n for n in names if n in MAPPED]


def world_rotation(obj, bone):
    return (obj.matrix_world @ bone.matrix_local).to_3x3().normalized()


def main():
    for item in items:
        parts = item.split(':')
        fbx, act_name = parts[0], parts[1]
        flags = {p for p in parts[2:] if p in ('turn', 'float', 'calm')}
        numbers = [float(p) for p in parts[2:] if p not in flags]
        trim = (numbers[0], numbers[1]) if numbers else None
        before, acts_before = set(bpy.data.objects), set(bpy.data.actions)
        bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
        fps_src = scene.render.fps / scene.render.fps_base
        new = set(bpy.data.objects) - before
        src = next(o for o in new if o.type == 'ARMATURE')
        pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
        sact = next(iter(set(bpy.data.actions) - acts_before))
        sbone = lambda n: src.data.bones[pre + n]
        # Yaw the source so its left side matches ours (+X): Mixamo characters face +Y after import.
        left_src = (src.matrix_world @ sbone('LeftUpLeg').head_local) - (src.matrix_world @ sbone('RightUpLeg').head_local)
        yaw = Matrix.Rotation(-math.atan2(left_src.y, left_src.x), 3, 'Z')
        src_rest = {n: yaw @ world_rotation(src, sbone(n)) for n in MAPPED}
        our_rest = {n: world_rotation(rig, rig.data.bones[n]) for n in MAPPED}
        align = {}
        for n in MAPPED:
            if n in ARMS:
                ours = our_rest[n] @ Vector((0, 1, 0))
                theirs = src_rest[n] @ Vector((0, 1, 0))
                align[n] = ours.rotation_difference(theirs).to_matrix()
            else:
                align[n] = Matrix.Identity(3)
        src_height = (src.matrix_world @ sbone('Head').head_local).z - (src.matrix_world @ sbone('LeftFoot').head_local).z
        our_height = (rig.matrix_world @ rig.data.bones['Head'].head_local).z - \
            (rig.matrix_world @ rig.data.bones['LeftFoot'].head_local).z
        ratio = our_height / src_height
        src.animation_data.action = sact
        f0, f1 = sact.frame_range
        t0, t1 = (0.0, (f1 - f0) / fps_src) if trim is None else trim
        frames = int(round((t1 - t0) * FPS))
        scene.frame_set(int(f0))
        hips0 = yaw @ (src.matrix_world @ src.pose.bones[pre + 'Hips'].head)
        rig.animation_data_create()
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis = Matrix()
        bpy.context.view_layer.update()
        our_hips0 = rig.matrix_world @ rig.pose.bones['Hips'].head
        if act_name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[act_name])
        act = bpy.data.actions.new(act_name)
        act.use_fake_user = True
        rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        turn = Matrix.Identity(3)
        if 'turn' in flags:
            scene.frame_set(int(math.floor(f0 + t0 * fps_src)))
            M = yaw @ (src.matrix_world @ src.pose.bones[pre + 'Spine2'].matrix).to_3x3().normalized()
            forward = (M @ src_rest['Spine2'].inverted() @ our_rest['Spine2']) @ \
                (our_rest['Spine2'].inverted() @ Vector((0, -1, 0)))
            turn = Matrix.Rotation(-math.atan2(forward.x, -forward.y), 3, 'Z')
        float_legs = {}
        if 'float' in flags:
            floating = bpy.data.actions['Floating']
            rig.animation_data.action = floating
            if getattr(floating, 'slots', None) is not None and len(floating.slots):
                rig.animation_data.action_slot = floating.slots[0]
            scene.frame_set(0)
            float_legs = {n: rig.pose.bones[n].matrix_basis.copy() for n in LEGS}
            rig.animation_data.action = None
            for pb in rig.pose.bones:
                pb.matrix_basis = Matrix()
            bpy.context.view_layer.update()
            rig.animation_data.action = act
        hips_start = None
        for i in range(frames + 1):
            sf = f0 + (t0 + i / FPS) * fps_src
            scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
            for n in order:
                pb = rig.pose.bones[n]
                if n in float_legs:
                    pb.rotation_mode = 'QUATERNION'
                    pb.matrix_basis = float_legs[n]
                    bpy.context.view_layer.update()
                    pb.keyframe_insert('rotation_quaternion', frame=i)
                    continue
                M = yaw @ (src.matrix_world @ src.pose.bones[pre + n].matrix).to_3x3().normalized()
                D = turn @ M @ src_rest[n].inverted()
                world = (D @ align[n] @ our_rest[n]).to_4x4()
                if n == 'Hips':
                    hips = turn @ yaw @ (src.matrix_world @ src.pose.bones[pre + 'Hips'].head)
                    if hips_start is None:
                        hips_start = hips.copy()
                    travel = hips - hips_start
                    if float_legs:
                        # Floating: no stepping or crouching travel sideways; keep half of the vertical bob.
                        travel = Vector((0.0, 0.0, 0.5 * travel.z))
                    world.translation = our_hips0 + travel * ratio
                else:
                    world.translation = rig.matrix_world @ pb.head
                pb.rotation_mode = 'QUATERNION'
                pb.matrix = rig.matrix_world.inverted() @ world
                if 'calm' in flags and n in CALM:
                    pb.rotation_quaternion = Quaternion().slerp(pb.rotation_quaternion, CALM[n])
                bpy.context.view_layer.update()
                pb.keyframe_insert('rotation_quaternion', frame=i)
                if n == 'Hips':
                    pb.keyframe_insert('location', frame=i)
        act.use_frame_range = True
        act.frame_start, act.frame_end = 0, frames
        rig.animation_data.action = None
        for obj in new:
            bpy.data.objects.remove(obj, do_unlink=True)
        for extra in set(bpy.data.actions) - acts_before - {act}:
            bpy.data.actions.remove(extra)
        print(f'RETARGET {act_name} <- {os.path.basename(fbx)} {t0:.2f}-{t1:.2f} s: {frames + 1} frames, '
              f'height ratio {ratio:.3f}')
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    scene.render.fps, scene.render.fps_base = FPS, 1
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)


main()
