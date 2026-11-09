"""m442: the wide blouse sleeves (forearm-weighted hems) hang beside the thighs and Mixamo's idle/walk bring the arms in,
so the hems went 6 cm into the thighs (g6_probe.py). Per listed clip and frame each upper arm turns out by ANG degrees
about the chest's forward axis (world, pivot at the shoulder joint; batch B's ARM_ABDUCT_DEG rule for set clips),
children follow. Args: -- <in blend> <out blend> <Action> ...  (env ARM_ABDUCT_DEG, default 8)"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
ANG = math.radians(float(os.environ.get('ARM_ABDUCT_DEG', '8')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    keys = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ch = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
        fwd = (ch.to_3x3() @ FWD).normalized()
        for s, sign in (('L', 1), ('R', -1)):                # +angle about -Y turns the left arm out (+X)
            pb = rig.pose.bones[f'B_{s}_UpperArm']
            M = rig.matrix_world @ pb.matrix; t = M.translation.copy()
            M = Matrix.Rotation(sign * ANG, 4, fwd) @ M; M.translation = t
            pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
            keys[(s, f)] = pb.rotation_quaternion.copy()
        rig.animation_data.action = act
    for (s, f), q in keys.items():
        pb = rig.pose.bones[f'B_{s}_UpperArm']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=f)
    print('ABDUCT', an, f0, f1, 'deg', round(math.degrees(ANG), 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
