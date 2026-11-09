"""Mixamo hit reaction -> the thief's Hit (user 2026-10-14: "hit - use better anim"), relative to the clip's own
first frame so neither rig's rest pose matters: each mapped bone takes the source's WORLD rotation change since frame 0,
D(t) = W(t) W(0)^-1, on top of the thief's Standing frame 0 (posed world = D(t) S); the hips also move by the source
hips' travel since frame 0, scaled by the leg-length ratio. Fingers, daggers and cloak chains keep Standing. The clip
is resampled to `frames` (24 fps; the native hit is 0.75 s = 18 frames) and eased back into Standing over the last
`settle` frames.
Usage: blender -b <blend> -P retarget_hit.py -- <out blend> <fbx>:<ActionName>[:frames[:settle]] [...]
(also used as a module by build_clips_thf.py: retarget(arm, fbx, frames, settle) -> list of poses)"""
import bpy, os, sys, math
from mathutils import Matrix, Vector, Quaternion

MAP = {'Hips': 'Hips', 'Spine': 'Spine', 'Spine1': 'Spine01', 'Spine2': 'Spine02', 'Neck': 'neck', 'Head': 'Head'}
for side in ('Left', 'Right'):
    for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase'):
        MAP[side + b] = side + b


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def retarget(arm, fbx, frames=18, settle=5, standing='Standing'):
    scene = bpy.context.scene
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx, automatic_bone_orientation=False)
    src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    act = src.animation_data.action
    f0, f1 = act.frame_range
    pref = next((p for p in ('mixamorig:', 'mixamorig1:', '') if p + 'Hips' in src.pose.bones), '')
    sb = {k: src.pose.bones[pref + k] for k in MAP if pref + k in src.pose.bones}
    src_fps = 30.0

    def src_world(t):
        scene.frame_set(int(t), subframe=t - int(t))
        return {k: (src.matrix_world @ pb.matrix).copy() for k, pb in sb.items()}

    def leg(world, side):
        return ((world[side + 'UpLeg'].translation - world[side + 'Leg'].translation).length
                + (world[side + 'Leg'].translation - world[side + 'Foot'].translation).length)

    W0 = src_world(f0)
    # the thief's Standing frame 0
    st = bpy.data.actions[standing]
    arm.animation_data.action = st
    if getattr(st, 'slots', None):
        arm.animation_data.action_slot = st.slots[0]
    scene.frame_set(0)
    S = {n: (arm.matrix_world @ arm.pose.bones[n].matrix).copy() for n in MAP.values()}
    base = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones}
    thief_leg = sum(((S[s + 'UpLeg'].translation - S[s + 'Leg'].translation).length
                     + (S[s + 'Leg'].translation - S[s + 'Foot'].translation).length) for s in ('Left', 'Right')) / 2
    ratio = thief_leg / ((leg(W0, 'Left') + leg(W0, 'Right')) / 2)
    order = [b.name for b in arm.data.bones if b.name in MAP.values()]          # parents first
    inv = {v: k for k, v in MAP.items()}
    arm.animation_data.action = None
    poses = []
    duration = (f1 - f0) / src_fps
    for i in range(frames + 1):
        t = f0 + (f1 - f0) * i / frames
        W = src_world(t)
        for pb in arm.pose.bones:
            pb.location, pb.rotation_quaternion = base[pb.name]
        bpy.context.view_layer.update()
        for n in order:
            k = inv[n]
            D = W[k].to_quaternion() @ W0[k].to_quaternion().inverted()
            R = (D @ S[n].to_quaternion()).to_matrix().to_4x4()
            pbn = arm.pose.bones[n]
            head = (arm.matrix_world @ pbn.matrix).translation
            if n == 'Hips':
                head = S[n].translation + (W[k].translation - W0[k].translation) * ratio
            M = Matrix.Translation(head) @ R
            pbn.matrix = arm.matrix_world.inverted() @ M
            bpy.context.view_layer.update()
        pose = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones}
        w = ease((frames - i) / settle) if i > frames - settle else 1.0      # settle back into Standing
        if w < 1.0:
            for n_, (l, q) in pose.items():
                lb, qb = base[n_]
                if qb.dot(q) < 0:
                    q = -q
                pose[n_] = (lb.lerp(l, w), qb.slerp(q, w))
        poses.append(pose)
    bpy.data.objects.remove(src)
    print('RETARGET', os.path.basename(fbx), 'source %.2f s ->' % duration, '%.2f s' % (frames / 24), 'leg ratio %.3f' % ratio)
    return poses


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    out, items = args[0], args[1:]
    arm = bpy.data.objects['Thief_Rig']
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    for item in items:
        parts = item.split(':')
        fbx, name = parts[0], parts[1]
        frames = int(parts[2]) if len(parts) > 2 else 18
        settle = int(parts[3]) if len(parts) > 3 else 5
        poses = retarget(arm, fbx, frames, settle)
        if name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[name])
        act = bpy.data.actions.new(name); act.use_fake_user = True
        arm.animation_data.action = act
        prev = {}
        for f, pose in enumerate(poses):
            for pb in arm.pose.bones:
                loc, q = pose[pb.name]
                if pb.name in prev and prev[pb.name].dot(q) < 0:
                    q = -q
                prev[pb.name] = q
                pb.location, pb.rotation_quaternion = loc, q
                pb.keyframe_insert('location', frame=f)
                pb.keyframe_insert('rotation_quaternion', frame=f)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
