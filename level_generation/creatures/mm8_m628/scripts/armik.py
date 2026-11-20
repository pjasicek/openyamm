"""Minimal-change arm IK for the source-frame rig (imported by the authoring scripts; runs inside Blender).

Starting from a reference pose (the clip's own frame), the arm is moved so that the wrist reaches a target with the
elbow in a given plane, by the smallest rotations: the upper arm swings onto the new shoulder -> elbow direction and
rolls about it by the change of the elbow-plane normal; the forearm is carried along and swings onto elbow -> wrist;
the hand takes a world orientation. The forearm keeps its roll relative to the upper arm (the source forearm is a
hinge; the hand carries the roll, distributed later by twist_bones.py).

Spear aim: hand_for_axis() returns the hand world rotation that points the grip axis (hand-local) along a direction,
choosing the roll about it that costs the least wrist bend (swing of the hand against the forearm, x1) and forearm
roll (x0.35), plus a continuity term to the previous choice."""
import math
import bpy
from mathutils import Vector, Quaternion, Matrix


def W(rig, n):
    return rig.matrix_world @ rig.pose.bones[n].matrix


def set_world(rig, n, M):
    rig.pose.bones[n].matrix = rig.matrix_world.inverted() @ M
    bpy.context.view_layer.update()


def rot_world(M, R3):
    """M (4x4 world) with its rotation replaced by R3 (3x3), translation kept."""
    out = R3.to_4x4(); out.translation = M.translation.copy(); return out


def solve(rig, side, wrist, pole=None, hand_rot=None, stretch_ok=0.999):
    """wrist: world target of the hand joint. pole: world point the elbow should bend toward (None keeps the reference
    elbow plane). hand_rot: world 3x3 of the hand (None keeps its world orientation). Returns the reach ratio."""
    ua, fa, hd = f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand'
    Mu, Mf, Mh = W(rig, ua), W(rig, fa), W(rig, hd)
    S, E0, W0 = Mu.translation.copy(), Mf.translation.copy(), Mh.translation.copy()
    if hand_rot is None:
        hand_rot = Mh.to_3x3().normalized()
    L1, L2 = (E0 - S).length, (W0 - E0).length
    T = Vector(wrist)
    d = T - S; dist = d.length; reach = dist / (L1 + L2)
    if dist > (L1 + L2) * stretch_ok:
        T = S + d.normalized() * (L1 + L2) * stretch_ok; d = T - S; dist = d.length
    u = d.normalized()
    # elbow plane: from the pole point, or the reference elbow's offset from the reference shoulder -> wrist line
    if pole is not None:
        p = Vector(pole) - S
    else:
        r = (W0 - S).normalized(); p = (E0 - S) - r * (E0 - S).dot(r)
        p = p if p.length > 1e-6 else Vector((0, 0, -1))
        p = (W0 - S).normalized().rotation_difference(u) @ p      # carried with the shoulder -> wrist change
    v = p - u * p.dot(u)
    v = v.normalized() if v.length > 1e-6 else u.orthogonal().normalized()
    ca = (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)
    ca = max(-1.0, min(1.0, ca))
    E = S + L1 * (u * ca + v * math.sqrt(max(0.0, 1 - ca * ca)))
    # upper arm: swing onto S->E, then roll so the reference elbow-plane normal maps onto the new one
    a0, a1 = (E0 - S).normalized(), (E - S).normalized()
    q = a0.rotation_difference(a1)
    n0 = (E0 - S).cross(W0 - E0); n1 = (E - S).cross(T - E)
    if n0.length > 1e-6 and n1.length > 1e-6:
        n0 = (q @ n0); n0 = (n0 - a1 * n0.dot(a1)).normalized(); n1 = (n1 - a1 * n1.dot(a1)).normalized()
        ang = math.atan2(a1.dot(n0.cross(n1)), n0.dot(n1))
        q = Quaternion(a1, ang) @ q
    set_world(rig, ua, rot_world(Mu, q.to_matrix() @ Mu.to_3x3().normalized()))
    Mf2 = W(rig, fa)                                               # forearm carried by the upper arm
    f0 = (W(rig, hd).translation - Mf2.translation).normalized()
    qf = f0.rotation_difference((T - Mf2.translation).normalized())
    set_world(rig, fa, rot_world(Mf2, qf.to_matrix() @ Mf2.to_3x3().normalized()))
    set_world(rig, hd, rot_world(W(rig, hd), hand_rot))
    return reach


def split_swing_twist(q, axis):
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def wrist_cost(rig, side, hand_rot):
    """(swing deg, twist deg) of the hand against the forearm, relative to the rest relation."""
    fa, hd = f'B_{side}_Forearm', f'B_{side}_Hand'
    Mf = W(rig, fa).to_3x3().normalized()
    rest_rel = (rig.data.bones[fa].matrix_local.to_3x3().inverted() @ rig.data.bones[hd].matrix_local.to_3x3())
    rel = rest_rel.inverted() @ (Mf.inverted() @ hand_rot)       # = the hand's local (basis) rotation
    sw, tw = split_swing_twist(rel.to_quaternion(), Vector((0, 1, 0)))
    return math.degrees(sw.angle if sw.angle <= math.pi else 2 * math.pi - sw.angle), math.degrees(tw)


def hand_for_axis(rig, side, axis_local, direction, prev_roll=None, step=5, k_twist=0.35, k_cont=0.4, twist_bias=0.0):
    """World 3x3 for the hand so that hand @ axis_local points along `direction`; returns (rot, roll, swing, twist)."""
    hd = f'B_{side}_Hand'
    H = W(rig, hd).to_3x3().normalized()
    dcur = (H @ Vector(axis_local)).normalized(); dn = Vector(direction).normalized()
    base = dcur.rotation_difference(dn).to_matrix() @ H
    best = None
    for k in range(-180, 180, step):
        R = Quaternion(dn, math.radians(k)).to_matrix() @ base
        sw, tw = wrist_cost(rig, side, R)
        c = sw + k_twist * abs(tw - twist_bias)
        if prev_roll is not None:
            dk = (k - prev_roll + 180) % 360 - 180
            c += k_cont * abs(dk)
        if best is None or c < best[0]:
            best = (c, R, k, sw, tw)
    return best[1], best[2], best[3], best[4]

