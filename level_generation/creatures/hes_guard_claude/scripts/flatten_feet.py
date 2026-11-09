"""Level the bare feet on the floor (Warlock: the set clips' ankles tilt the modelled flat bare feet about 20 degrees
toe-down, so she stood on tiptoe; user review 2026-10-20). Per frame of each listed clip, each foot bone's world
rotation is turned toward its rest orientation (the A-pose mesh stands flat) keeping the foot's current heading:
fully while the ankle is within LOW of its rest height, fading out by HIGH above it, so a stepping foot keeps the
clip's own lift and roll in the air. A grounded ankle below its rest height is raised toward it by the same weight
(two-bone leg solve, the knee keeps its bending plane): the set's idle and casts bend the knees, and the levelled
soles went 3-8 cm under the floor. The toes ride on the foot (local rotation unchanged).
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
LOW, HIGH = 0.02, 0.08
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world


def setw(n, M):
    rig.pose.bones[n].matrix = AW.inverted() @ M
    bpy.context.view_layer.update()


def turn(n, R3, pivot):
    M = AW @ rig.pose.bones[n].matrix
    setw(n, Matrix.Translation(pivot) @ R3.to_4x4() @ Matrix.Translation(-pivot) @ M)


def leg_ik(s, T):
    th, ca, ft = (f'B_{s}_{b}' for b in ('Thigh', 'Calf', 'Foot'))
    H = (AW @ rig.pose.bones[th].matrix).translation; K = (AW @ rig.pose.bones[ca].matrix).translation
    A = (AW @ rig.pose.bones[ft].matrix).translation
    l1, l2 = (K - H).length, (A - K).length
    d = min((T - H).length, l1 + l2 - 1e-4); u = (T - H).normalized()
    p = (K - H) - u * (K - H).dot(u)
    if p.length < 1e-6:
        return
    p.normalize()
    al = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    K2 = H + (u * math.cos(al) + p * math.sin(al)) * l1
    turn(th, (K - H).rotation_difference(K2 - H).to_matrix(), H)
    A1 = (AW @ rig.pose.bones[ft].matrix).translation
    turn(ca, (A1 - K2).rotation_difference(H + u * d - K2).to_matrix(), K2)


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


REST = {s: (AW.to_3x3() @ rig.data.bones[f'B_{s}_Foot'].matrix_local.to_3x3()).normalized() for s in 'LR'}
H0 = {s: (AW @ rig.data.bones[f'B_{s}_Foot'].head_local).z for s in 'LR'}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = 0.0; lift = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for s in 'LR':
            n = f'B_{s}_Foot'; pb = rig.pose.bones[n]
            M = AW @ pb.matrix
            w = 1.0 - sstep((M.translation.z - H0[s] - LOW) / (HIGH - LOW))
            if w <= 0:
                continue
            D = M.to_3x3().normalized() @ REST[s].inverted()
            fwd = D @ Vector((0, -1, 0))
            psi = math.atan2(fwd.x, -fwd.y)
            Dq = D.to_quaternion(); Tq = Matrix.Rotation(psi, 3, 'Z').to_quaternion()
            if Dq.dot(Tq) < 0:
                Tq.negate()
            worst = max(worst, math.degrees(Dq.rotation_difference(Tq).angle) * w)
            Rf = Dq.slerp(Tq, w).to_matrix() @ REST[s]
            if M.translation.z < H0[s]:
                T = M.translation.copy(); T.z += (H0[s] - T.z) * w
                leg_ik(s, T)
                lift = max(lift, (T.z - M.translation.z) * 100)
            M2 = AW @ pb.matrix; R = Rf.to_4x4(); R.translation = M2.translation
            setw(n, R)
            for b in ('Thigh', 'Calf', 'Foot'):
                q = rig.pose.bones[f'B_{s}_{b}']; q.rotation_mode = 'QUATERNION'; q.keyframe_insert('rotation_quaternion', frame=f)
    print('FEET', name, 'frames', f1 - f0 + 1, 'max levelling deg', round(worst, 1), 'max ankle lift cm', round(lift, 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
