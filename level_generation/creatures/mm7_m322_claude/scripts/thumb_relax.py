"""Open-hand thumb relax (m302 G5): the left hand stays open (no prop), but the source clips curl its thumb toward the
palm, which our thicker, differently aimed thumb (HANDFRAME L thumb 84 deg off the source) turns into a 4.4-4.8x
stretch at the thumb web. Every clip's B_<SIDE>_Finger0/01/02 rotations are slerped toward rest by K (keep 1-K of the
source curl). Args: -- <in> <out>   env SIDE (L), K (0.5)"""
import bpy, sys, os
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
SIDE, K = os.environ.get('SIDE', 'L'), float(os.environ.get('K', '0.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
BONES = [f'B_{SIDE}_Finger0', f'B_{SIDE}_Finger01', f'B_{SIDE}_Finger02']
BONES = [b if b in rig.pose.bones else b.replace('Finger01', 'Finger0.001').replace('Finger02', 'Finger0.002') for b in BONES]   # the set's right-thumb names
for act in bpy.data.actions:
    fcs = [fc for fc in act.fcurves if any(fc.data_path == f'pose.bones["{b}"].rotation_quaternion' for b in BONES)] \
        if hasattr(act, 'fcurves') else []
    if not fcs:
        rig.animation_data_create(); rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    keyed = {}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        keyed[f] = {b: rig.pose.bones[b].rotation_quaternion.copy() for b in BONES}
    for f, qs in keyed.items():
        for b, q in qs.items():
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion().slerp(q if q.w >= 0 else -q, 1 - K)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'THUMB {act.name}: {SIDE} thumb curl kept {1 - K:.2f} over {f1 - f0 + 1} frames')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
