"""Plant retargeted set clips on Standing (the set's Unarmed clips stand in a wide fighting stance; the native cleric
casts upright, and under the floor-length robe a lunge only shows as a sliding hem).
Per frame: legs (local) and the pelvis position hold Standing's frame 0; the pelvis rotation keeps PELVIS_TURN of the
source pelvis's rotation change from its own frame 0; every other bone keeps its source WORLD rotation turned by a
constant yaw that aligns the source chest at frame 0 with Standing's chest (as retarget_mixamo.py ':plant'), and
DROP of the source pelvis height change is kept (a small sink on effort). Keys in place.
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
PELVIS_TURN = float(os.environ.get('PELVIS_TURN', '0.35'))
DROP = float(os.environ.get('DROP', '0.25'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; AW = rig.matrix_world
names = [b.name for b in rig.data.bones if b.name.startswith('B_')]
LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
UPPER = [n for n in names if n not in LEGS and n != 'B_Pelvis']
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
yaw_of = lambda R: math.atan2((R @ CHEST_FWD).y, (R @ CHEST_FWD).x)


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


use(bpy.data.actions['Standing']); scene.frame_set(0)
st_pel = (AW @ rig.pose.bones['B_Pelvis'].matrix).copy()
st_chest = (AW @ rig.pose.bones['B_Spine2'].matrix).to_3x3().normalized()
st_legs = {n: rig.pose.bones[n].matrix_basis.copy() for n in LEGS}
for name in acts:
    act = bpy.data.actions[name]; use(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    rec = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        rec.append({n: (AW @ rig.pose.bones[n].matrix).copy() for n in names})
    C = Matrix.Rotation(yaw_of(st_chest) - yaw_of(rec[0]['B_Spine2'].to_3x3().normalized()), 3, 'Z')
    p0 = rec[0]['B_Pelvis']
    for i, f in enumerate(range(f0, f1 + 1)):
        R = rec[i]
        dq = (R['B_Pelvis'].to_3x3().normalized() @ p0.to_3x3().normalized().inverted()).to_quaternion()
        dq = Quaternion().slerp(dq, PELVIS_TURN)
        M = (dq.to_matrix() @ st_pel.to_3x3().normalized()).to_4x4()
        M.translation = st_pel.translation + Vector((0, 0, DROP * (R['B_Pelvis'].translation.z - p0.translation.z)))
        pb = rig.pose.bones['B_Pelvis']; pb.rotation_mode = 'QUATERNION'
        pb.matrix = AW.inverted() @ M; bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        for n in LEGS:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = st_legs[n]
            pb.keyframe_insert('rotation_quaternion', frame=f)
        bpy.context.view_layer.update()
        for n in UPPER:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            Mn = (C @ R[n].to_3x3().normalized()).to_4x4(); Mn.translation = AW @ pb.head
            pb.matrix = AW.inverted() @ Mn; bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('PLANT', name, 'frames', f1 - f0 + 1, 'yaw deg', round(math.degrees(math.atan2(C[1][0], C[0][0])), 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
