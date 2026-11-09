"""m178: plant both feet in the standing clips. The retargeted Mixamo Standard Idle keeps its left foot 1.7 cm higher
than the right (3.2 vs 1.5 cm) and the floor pass grounds only the lower one, so the left sole hovered 2.7 cm in
Standing and in the attack/fidget planted on it (sole gate). Per listed action and frame, the lower foot's ankle is
lifted by the difference of the two feet's lowest vertices with a two-bone leg IK (thigh swings onto the new
hip -> knee direction keeping the knee plane, calf onto knee -> ankle, foot keeps its world orientation).
Args: -- <in blend> <out blend> <Action> ..."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
vg = [g.name for g in body.vertex_groups]
FV = {s: np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > 0.5 for v in me.vertices]) for s in 'LR'}
W = lambda n: rig.matrix_world @ rig.pose.bones[n].matrix


def set_world(n, M):
    rig.pose.bones[n].matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()


def rot_world(M, R3):
    o = R3.to_4x4(); o.translation = M.translation.copy(); return o


def lows():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
    return {s: float(z[FV[s]].min()) for s in 'LR'}


def leg_ik(s, dz):
    th, ca, ft = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
    Mt, Mc, Mf = W(th), W(ca), W(ft)
    S, K0, A0 = Mt.translation.copy(), Mc.translation.copy(), Mf.translation.copy()
    foot_rot = Mf.to_3x3().normalized()
    T = A0 + Vector((0, 0, dz)); L1, L2 = (K0 - S).length, (A0 - K0).length
    d = T - S; dist = min(d.length, (L1 + L2) * 0.999); u = d.normalized(); T = S + u * dist
    r = (A0 - S).normalized(); p = (K0 - S) - r * (K0 - S).dot(r)
    p = r.rotation_difference(u) @ p; v = (p - u * p.dot(u)).normalized()
    c = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    K = S + L1 * (u * c + v * math.sqrt(1 - c * c))
    q = (K0 - S).normalized().rotation_difference((K - S).normalized())
    set_world(th, rot_world(Mt, q.to_matrix() @ Mt.to_3x3().normalized()))
    Mc2 = W(ca); q2 = (W(ft).translation - Mc2.translation).normalized().rotation_difference((T - Mc2.translation).normalized())
    set_world(ca, rot_world(Mc2, q2.to_matrix() @ Mc2.to_3x3().normalized()))
    set_world(ft, rot_world(W(ft), foot_rot))


LEG = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]
for an in acts:
    act = bpy.data.actions[an]; f0, f1 = (int(x) for x in act.frame_range); keys = []; worst = 0.0
    for f in range(f0, f1 + 1):
        rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]; sc.frame_set(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        rig.animation_data.action = None
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        bpy.context.view_layer.update()
        for _ in range(2):
            # the higher leg is already near full extension (its ankle cannot go lower): the LOWER foot is lifted
            # to the same height by bending its knee; the floor pass then lowers the pelvis onto both soles
            lo = lows(); low = min('LR', key=lambda s: lo[s]); dz = max(lo.values()) - lo[low]
            if dz > 0.002:
                leg_ik(low, dz)
        lo = lows(); worst = max(worst, abs(lo['L'] - lo['R']))
        keys.append({n: rig.pose.bones[n].rotation_quaternion.copy() for n in LEG})
    rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    for i, f in enumerate(range(f0, f1 + 1)):
        for n, q in keys[i].items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None
    print(f'FEET {an}: both feet planted, residual difference of the lowest sole points {worst * 100:.2f} cm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
