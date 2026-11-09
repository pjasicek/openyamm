"""Posture fix after the retarget (user review: shoulders slumped forward in the idle and the hit). The Mixamo idle and
the set's hit carry the source body's rounded shoulders: the shoulder joints sat 3-7 cm IN FRONT of the neck base and
3-6 cm lower, where our rest pose has them 5.5 cm behind it (posture_probe.py). Per frame of every listed clip:
- each clavicle's rotation relative to B_Spine2 becomes its REST relation plus KEEP of the clip's own clavicle motion
  (slerp), so a shrug or a reach still shows;
- the upper arm keeps its WORLD rotation (the retarget's arm direction), so only the shoulder joint moves back;
- head/neck: the change of B_Neck and B_Head from Standing frame 0 is scaled by NECK_KEEP in the clips listed in
  NECK_CLIPS (the hit snapped the head 66 deg down).
Args: -- <in blend> <out blend> clip[:keep] [...]"""
import bpy, sys, os
from mathutils import Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, clips = a[0], a[1], a[2:]
KEEP = float(os.environ.get('CLAV_KEEP', '0.25'))
NECK_KEEP = float(os.environ.get('NECK_KEEP', '0.5'))
NECK_CLIPS = os.environ.get('NECK_CLIPS', 'Hit').split(',')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
PB = rig.pose.bones; B = rig.data.bones


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


rest_rel = {s: B['B_Spine2'].matrix_local.inverted() @ B[f'B_{s}_Clavicle'].matrix_local for s in 'LR'}
for item in clips:
    c, _, kk = item.partition(':'); keep = float(kk) if kk else KEEP
    act = bpy.data.actions[c]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    ref = None
    if c in NECK_CLIPS:
        set_act(bpy.data.actions['Standing']); scene.frame_set(0)
        ref = {n: PB[n].matrix_basis.to_quaternion() for n in ('B_Neck', 'B_Head')}
        set_act(act)
    keys = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        new = {}
        for s in 'LR':
            cl, ua = PB[f'B_{s}_Clavicle'], PB[f'B_{s}_UpperArm']
            ua_world = ua.matrix.copy()
            rel = PB['B_Spine2'].matrix.inverted() @ cl.matrix
            q = rest_rel[s].to_quaternion().slerp(rel.to_quaternion(), keep)
            Mrel = q.to_matrix().to_4x4(); Mrel.translation = rel.translation
            cl.matrix = PB['B_Spine2'].matrix @ Mrel
            bpy.context.view_layer.update()
            ua.matrix = ua_world
            bpy.context.view_layer.update()
            new[cl.name] = cl.matrix_basis.to_quaternion(); new[ua.name] = ua.matrix_basis.to_quaternion()
        if ref is not None:
            for n in ('B_Neck', 'B_Head'):
                cur = PB[n].matrix_basis.to_quaternion()
                d = ref[n].rotation_difference(cur)
                new[n] = ref[n] @ Quaternion().slerp(d, NECK_KEEP)
        keys.append((f, new))
    for f, new in keys:
        for n, q in new.items():
            pb = PB[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('CLAVFIX', c, 'frames', f1 - f0 + 1, 'keep', keep, 'neck' if ref is not None else '')
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
