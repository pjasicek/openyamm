"""Soft cap on how high an arm rises (m422 user review 1: the attack's wind-up lifted the right claw straight overhead,
wrist at 1.76 m, and the coat armpit and side panel stretched into a flat fan; the native raises the claw above the
head, not fully vertical). Per frame of the listed clips, per side: the upper arm's elevation from the chest's down
axis beyond KNEE deg is compressed (elev' = KNEE + (elev - KNEE) * GAIN) by turning the upper arm about the axis
perpendicular to the chest-down axis and the arm; the forearm and hand keep their local rotations (they ride along),
and the clavicle's elevation against Standing frame 0 is clamped to CLAV deg (playbook: clavicle reach <= 8 deg).
Keys every frame (quaternions). Args: -- <in blend> <out blend> <clip> [...]"""
import bpy, sys, os, math
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, clips = a[0], a[1], a[2:]
KNEE, GAIN, CLAV = float(os.environ.get('KNEE', '95')), float(os.environ.get('GAIN', '0.35')), float(os.environ.get('CLAV', '8'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world


def W(n):
    return AW @ rig.pose.bones[n].matrix


def setw(n, M):
    rig.pose.bones[n].matrix = AW.inverted() @ M; bpy.context.view_layer.update()


def chest_frame():
    C = W('B_Spine2'); R = C.to_3x3().normalized() @ rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
    return R @ Vector((0, 0, -1)), R


st = bpy.data.actions['Standing']; rig.animation_data_create(); rig.animation_data.action = st
if len(st.slots): rig.animation_data.action_slot = st.slots[0]
scene.frame_set(0)
CL0 = {s: (W(f'B_{s}_Clavicle').to_3x3().normalized(), ) for s in 'LR'}
down0, R0 = chest_frame()
CLDIR0 = {s: (R0.inverted() @ ((W(f'B_{s}_UpperArm').translation - W(f'B_{s}_Clavicle').translation).normalized())) for s in 'LR'}
for name in clips:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range); worst = {}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        down, R = chest_frame()
        for s in 'LR':
            # clavicle: elevation of the clavicle direction (in the chest frame) against Standing, clamped to CLAV
            c = W(f'B_{s}_Clavicle'); d = (R.inverted() @ (W(f'B_{s}_UpperArm').translation - c.translation)).normalized()
            el = math.degrees(math.asin(max(-1, min(1, d.z)))) - math.degrees(math.asin(max(-1, min(1, CLDIR0[s].z))))
            if el > CLAV:
                ax = (R @ d.cross(Vector((0, 0, 1)))).normalized()
                q = Quaternion(ax, -math.radians(el - CLAV))
                M = c.copy(); setw(f'B_{s}_Clavicle', Matrix.Translation(M.translation) @ q.to_matrix().to_4x4() @ Matrix.Translation(-M.translation) @ M)
            # upper arm elevation from the chest-down axis
            u = W(f'B_{s}_UpperArm'); e = W(f'B_{s}_Forearm').translation - u.translation
            elev = math.degrees(e.angle(down))
            worst[s] = max(worst.get(s, 0), elev)
            if elev > KNEE:
                tgt = KNEE + (elev - KNEE) * GAIN
                ax = e.cross(down)
                if ax.length > 1e-6:
                    q = Quaternion(ax.normalized(), math.radians(elev - tgt))
                    M = u.copy(); setw(f'B_{s}_UpperArm', Matrix.Translation(M.translation) @ q.to_matrix().to_4x4() @ Matrix.Translation(-M.translation) @ M)
        for s in 'LR':
            for b in ('Clavicle', 'UpperArm'):
                pb = rig.pose.bones[f'B_{s}_{b}']; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
    print('ARMCAP', name, 'max elevation before deg', {k: round(v, 1) for k, v in worst.items()}, 'knee', KNEE, 'gain', GAIN)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
