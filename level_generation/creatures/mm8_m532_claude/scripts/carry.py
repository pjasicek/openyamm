"""Bow-hand carry with a straight wrist (2026-10-19 user review of the bow wrist: "ok fix the wrist first").

The original clips placed the bow and derived the hand from it through the fitted grip, which bent the bow-hand wrist
114-168 deg. Here the bow keeps its pose (centre, limbs, string side) and the fist turns about the stave: the hand
orbits the stave, the arm is re-solved so the forearm runs into the hand, and the bow turns back by the same angle in
the fist, so only how the hand holds it changes. Shared by carry_fix.py (all clips) and animate_attack_v2.py (the
Attack's start and end hold)."""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix
import os
ELBOW_OUT = float(os.environ.get('CARRY_ELBOW_OUT', '.20'))     # 20 cm: the hanging upper arm clears the lat (5-15 cm pressed in 6-28 mm)


def _rot(axis, ang):
    """Rodrigues rotations about one unit axis for an array of angles -> (n, 3, 3)."""
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    s = np.sin(ang)[:, None, None]; c = np.cos(ang)[:, None, None]
    return np.eye(3)[None] + s * k[None] + (1 - c) * (k @ k)[None]


def grid(S, la, lf, B, grip, centre_local, out, up, fwd, floor_z=-1., upright=1.):
    """Every fist angle about the stave (2.5 deg) and elbow swivel (5 deg) for a bow at world matrix B (limbs = local
    Y) with its grip centre at B's translation. grip = bow rest rotation in the hand frame, centre_local = bow centre in
    the hand frame, S = shoulder, out/up/fwd = the chest's left, up and forward directions. Cost: wrist bend (forearm
    against the hand axis) plus penalties: elbow at least 12 cm under the shoulder, ELBOW_OUT (20 cm) out from it, within
    10 cm forward and 3 cm back of it (these three scaled by `upright`, 0 for a body lying on its side), wrist and
    elbow above floor_z. Returns hands (n,3,3), wrists (n,3), elbows (n,m,3), bends and costs (n,m)."""
    Bm = np.array(B.to_3x3()); c = np.array(B.translation); S = np.array(S)
    L = Bm[:, 1] / np.linalg.norm(Bm[:, 1]); G = np.array(grip); cl = np.array(centre_local)
    H0 = Bm @ np.linalg.inv(G)                                      # the hand of the original rigid grip
    H = _rot(L, np.radians(np.arange(-180, 180, 2.5))) @ H0[None]   # fist turned about the stave
    W = c[None] - H @ cl                                            # wrist for each fist angle
    d = W - S[None]; D = np.linalg.norm(d, axis=1); u = d / D[:, None]
    ok = D < (la + lf) * .999
    ca = np.clip((la * la + D * D - lf * lf) / (2 * la * D), -1, 1); r = la * np.sqrt(1 - ca * ca)
    m = S[None] + u * (la * ca)[:, None]
    p = np.cross(u, np.array(up)[None]); p /= np.linalg.norm(p, axis=1)[:, None]; q = np.cross(u, p)
    ths = np.radians(np.arange(0, 360, 5))
    E = m[:, None] + r[:, None, None] * (np.cos(ths)[None, :, None] * p[:, None] + np.sin(ths)[None, :, None] * q[:, None])
    f = (W[:, None] - E) / lf                                       # forearm direction
    bend = np.degrees(np.arccos(np.clip(np.einsum('pk,ptk->pt', H[:, :, 1], f), -1, 1)))
    rel = E - S[None, None]
    low = np.maximum(0, rel @ np.array(up) + .12)
    inward = np.maximum(0, ELBOW_OUT - rel @ np.array(out))         # upper arm clear of the flank and the lat
    forward = np.maximum(0, rel @ np.array(fwd) - .10) + np.maximum(0, -(rel @ np.array(fwd)) - .03)   # nor drawn back
    floor = np.maximum(0, floor_z - E[..., 2]) + np.maximum(0, floor_z - W[:, 2])[:, None]
    cost = bend + upright * (400 * low + 600 * inward + 150 * forward) + 2000 * floor
    cost[~ok] = np.inf
    return H, W, E, bend, cost


def solve(S, la, lf, B, grip, centre_local, out, up, fwd):
    """The cheapest hold of grid(): (hand rotation, wrist, elbow, bend, cost)."""
    H, W, E, bend, cost = grid(S, la, lf, B, grip, centre_local, out, up, fwd)
    i, j = np.unravel_index(np.argmin(cost), cost.shape)
    return Matrix(H[i].tolist()), Vector(W[i]), Vector(E[i, j]), float(bend[i, j]), float(cost[i, j])


def roll_twist(rig, rest, child, parent):
    """Twist of `child` about its own axis against `parent`, relative to the rest pose (degrees, -180..180)."""
    pb = rig.pose.bones
    rel = pb[parent].matrix.to_3x3().normalized().inverted() @ pb[child].matrix.to_3x3().normalized()
    rrel = rest[parent].to_3x3().inverted() @ rest[child].to_3x3()
    q = (rrel.inverted() @ rel).to_quaternion()
    return (math.degrees(2 * math.atan2(q[2], q[0])) + 180) % 360 - 180


def _steps(roll, name):
    """Full 4 deg search on a clip's first frame, then 1 deg steps near the previous frame's roll (no flicker)."""
    if not roll.get('_seeded_' + name):
        roll['_seeded_' + name] = True; return range(-360, 361, 4)
    return range(roll[name] - 16, roll[name] + 17)


def settle_roll(rig, Q, rest, side, k, roll):
    """Distribute the arm's roll without moving the elbow, hand or fingers: the upper arm turns about its own axis to
    the roll with the least elbow twist, then the forearm turns about its axis to split the remaining twist evenly
    between elbow and wrist (no twist bones: a 180 deg wrist candy-wraps the bracer). k scales the correction; `roll`
    keeps the previous frame's choice for continuity."""
    if k < 1e-4:
        return
    pb = rig.pose.bones; A, F, Hn = side + 'Arm', side + 'ForeArm', side + 'Hand'
    saved = {n: pb[n].matrix.copy() for n in (A, F, Hn)}; tip = pb[F].tail.copy()

    def restore(names):
        for n in names:
            pb[n].matrix = saved[n]; bpy.context.view_layer.update()

    def spin(name, degrees):
        b = pb[name]; Q.rotate_world(rig, name, (b.tail - b.head).normalized(), degrees)

    def try_arm(d):
        restore((A, F, Hn)); spin(A, d); Q.aim_bone(rig, F, tip); return abs(roll_twist(rig, rest, F, A))
    best = min(_steps(roll, A), key=lambda d: try_arm(d) + .35 * abs(d - roll[A]))
    roll[A] = best
    restore((A, F, Hn)); spin(A, best * k); Q.aim_bone(rig, F, tip)
    saved[F] = pb[F].matrix.copy(); restore((Hn,))

    def try_fore(d):
        pb[F].matrix = saved[F]; bpy.context.view_layer.update(); spin(F, d); restore((Hn,))
        return max(abs(roll_twist(rig, rest, F, A)), abs(roll_twist(rig, rest, Hn, F)))
    best = min(_steps(roll, F), key=lambda d: try_fore(d) + .35 * abs(d - roll[F]))
    roll[F] = best
    pb[F].matrix = saved[F]; bpy.context.view_layer.update(); spin(F, best * k); restore((Hn,))


def body_axes(rig, rest):
    """The chest's left (+X at rest), up and forward (-Y at rest) directions in the current pose."""
    R = rig.pose.bones['Chest'].matrix.to_3x3().normalized() @ rest['Chest'].to_3x3().inverted()
    return R @ Vector((1, 0, 0)), R @ Vector((0, 0, 1)), R @ Vector((0, -1, 0))


def carry_matrix(center=(.52, -.87, 1.43), axis=(0, -.14, 1), normal=(0, -1, 0)):
    """The Standing bow pose of animate.py (limbs along `axis`, local Z toward `normal`) as a 4x4 matrix."""
    y = Vector(axis).normalized(); z = Vector(normal); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    B = Matrix((x, y, z)).transposed().to_4x4(); B.translation = Vector(center); return B


BOW_POINTS = [Vector((0, y, z)) for y in (-.95, -.5, 0, .5, .95) for z in (.04, -.16)]   # stave and string, bow frame


def candidates(rig, rest, G, B, free=None, keep=48):
    """Holds for one frame: per fist angle its best elbow swivel, the `keep` cheapest. Each is a dict with the cost,
    hand rotation, wrist, elbow, bend, bow matrix and the bow change (a1, a2, k). With free = {'floor': z} the bow may
    also tilt about its grip (up to 60 deg, every 15 deg about the two axes across its limbs, 0.4 per degree) and come
    up to a quarter of the way toward the shoulder (slack arm, 60 per unit), bow and arm (7 cm radius) above the floor:
    a falling archer's grip gives way rather than his wrist (Death)."""
    pb = rig.pose.bones; out, up, fwd = body_axes(rig, rest)
    grip = Matrix(G['rest_hand_matrix']).to_3x3().inverted() @ Matrix(G['bow_rest_matrix']).to_3x3()
    S = pb['LArm'].head; args = (S, pb['LArm'].length, pb['LForeArm'].length)
    bows = [(B, 0, 0, 0.)]
    if free is not None:
        R = B.to_3x3(); bows = []
        for k in (0, .12, .25):
            for a1 in range(-60, 61, 15):
                for a2 in range(-60, 61, 15):
                    Bk = (Matrix.Rotation(math.radians(a1), 3, R.col[0]) @ Matrix.Rotation(math.radians(a2), 3, R.col[2])
                          @ R).to_4x4()
                    Bk.translation = B.translation.lerp(S, k)
                    if min((Bk @ p).z for p in BOW_POINTS) >= free['floor']:
                        bows.append((Bk, a1, a2, k))
    found = []
    for Bk, a1, a2, k in bows:
        H, W, E, bend, cost = grid(*args, Bk, grip, G['centre_hand_local'], out, up, fwd,
                                   -1. if free is None else free['floor'] + .07, max(0., up.z) ** 2)
        extra = .4 * (abs(a1) + abs(a2)) + 60 * k
        j = np.argmin(cost, axis=1)
        for i in np.argsort(cost[np.arange(len(j)), j])[:keep]:
            c = float(cost[i, j[i]])
            if np.isfinite(c):
                found.append({'cost': c + extra, 'H': Matrix(H[i].tolist()), 'W': Vector(W[i]), 'E': Vector(E[i, j[i]]),
                              'bend': float(bend[i, j[i]]), 'B': Bk.copy(), 'bow': (a1, a2, k)})
    found.sort(key=lambda x: x['cost'])
    return found[:keep]


def step_cost(x, y):
    """Continuity between holds of consecutive frames: hand axis, elbow and bow change."""
    hy = math.degrees(x['H'].col[1].angle(y['H'].col[1], 0.))
    bow = .8 * (abs(x['bow'][0] - y['bow'][0]) + abs(x['bow'][1] - y['bow'][1])) + 200 * abs(x['bow'][2] - y['bow'][2])
    return .6 * hy + 300 * (x['E'] - y['E']).length + bow


def path(frames, pin_start=True, pin_end=False):
    """Cheapest sequence of holds over a clip (dynamic programming over each frame's candidates). Pinned ends take the
    frame's cheapest hold, the one Standing and Attack use, so clips that start or end in the Standing pose meet it."""
    inf = float('inf')
    total = [c['cost'] if (i == 0 or not pin_start) else inf for i, c in enumerate(frames[0])]; back = []
    for f in range(1, len(frames)):
        cur, ptr = [], []
        for y in frames[f]:
            best = min(range(len(frames[f - 1])), key=lambda i: total[i] + step_cost(frames[f - 1][i], y))
            cur.append(total[best] + step_cost(frames[f - 1][best], y) + y['cost']); ptr.append(best)
        total = cur; back.append(ptr)
    i = 0 if pin_end else min(range(len(total)), key=lambda k: total[k]); out = [i]
    for ptr in reversed(back):
        i = ptr[i]; out.append(i)
    return [frames[f][i] for f, i in enumerate(reversed(out))]


def apply(rig, Q, rest, hold_, roll=None):
    """Pose the left arm and the bow for one hold; the arm starts from rest like a clip posed from rest (Attack)."""
    pb = rig.pose.bones
    for n in ('LArm', 'LForeArm', 'LHand'):
        pb[n].rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    Q.two_bone_ik(rig, 'LArm', 'LForeArm', hold_['W'], hold_['E'])
    b = pb['LHand']; b.matrix = Matrix.Translation(b.head) @ hold_['H'].to_4x4(); bpy.context.view_layer.update()
    if roll is not None:
        settle_roll(rig, Q, rest, 'L', 1., roll)
    pb['Bow'].matrix = hold_['B']; bpy.context.view_layer.update()
