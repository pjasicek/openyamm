"""Narrower stance (from mm6_dru1_claude/scripts/narrow_stance.py). m286 v2: the native m286sa0 stands with the hooves
under the hips (centres 0.27 H apart); Mixamo Orc Idle and the planted clips copy its wide stance. In each listed
clip every frame turns each thigh toward the midline by DEG (per clip: Name:deg) about the pelvis's forward axis
(at the hip joint), and each foot keeps its world rotation (soles stay flat). Local keys are
computed from armature-space matrices (no posing with the action attached). Args: -- <in blend> <out blend> [Clip[:deg] ...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector, Quaternion
_a = sys.argv[sys.argv.index('--') + 1:]
src, out = _a[:2]
DEG = float(os.environ.get('STANCE_DEG', '4.0'))
CLIPS = {c.split(':')[0]: float(c.split(':')[1]) if ':' in c else DEG for c in _a[2:]} or {n: DEG for n in ('Standing', 'Attack', 'Cast', 'Hit')}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))


def basis(bn, P_pose, B_pose):
    b = rig.data.bones[bn]
    rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
    return rest_rel.inverted() @ (P_pose.inverted() @ B_pose)


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


for name, DEGC in CLIPS.items():
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    keys = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        pb = rig.pose.bones
        pel = pb['B_Pelvis'].matrix.copy()
        fwd = (pel.to_3x3() @ PEL_FWD).normalized()
        frame = {}
        for s, sign in (('L', -1.0), ('R', 1.0)):          # +angle about forward turns a hanging leg toward +X
            T, C, F = pb[f'B_{s}_Thigh'].matrix.copy(), pb[f'B_{s}_Calf'].matrix.copy(), pb[f'B_{s}_Foot'].matrix.copy()
            hip = T.translation.copy()
            Rm = Matrix.Translation(hip) @ Matrix.Rotation(sign * math.radians(DEGC), 4, fwd) @ Matrix.Translation(-hip)
            T2 = Rm @ T; C2 = Rm @ C
            F2 = (Rm @ F)
            F2 = Matrix.Translation(F2.translation) @ F.to_3x3().normalized().to_4x4()   # sole keeps its world rotation
            frame[f'B_{s}_Thigh'] = basis(f'B_{s}_Thigh', pb[f'B_{s}_Thigh'].parent.matrix, T2).to_quaternion()
            frame[f'B_{s}_Foot'] = basis(f'B_{s}_Foot', C2, F2).to_quaternion()
        keys.append((f, frame))
    rig.animation_data.action = None
    set_act(act)
    for f, frame in keys:
        for bn, q in frame.items():
            p = rig.pose.bones[bn]; p.rotation_mode = 'QUATERNION'; p.rotation_quaternion = q
            p.keyframe_insert('rotation_quaternion', frame=f)
    print('STANCE', name, 'frames', len(keys), 'thighs turned in', DEGC, 'deg')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
