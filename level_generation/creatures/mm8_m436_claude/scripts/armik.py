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


def solve(rig, side, wrist, pole=None, hand_rot=None, stretch_ok=0.975):
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


def solve_aimed(rig, side, wrist, axis_local, direction, ref_snapshot, prev=None, phis=range(-80, 81, 10),
                devs=((0, 0),), k_twist=0.35, twist_neutral=30.0, k_phi=0.15, k_dev=0.6, k_cont=(0.3, 0.25, 0.3),
                fixed=None):
    """Arm + hand for a wrist target and a spear direction, choosing the elbow plane (phi: rotation of the reference
    elbow plane about the shoulder -> wrist line, deg), a deviation of the spear from `direction` (pitch/yaw deg, a
    small cone) and the hand roll by the least cost: wrist swing + k_twist |hand twist - twist_neutral| + k_phi |phi| +
    k_dev |dev| + continuity to `prev` (phi, roll, dev). ref_snapshot: {bone: matrix_basis} of the reference pose
    (restored before every trial). fixed=(phi, dev) skips the search for those. Returns dict."""
    ua, fa, hd = f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand'

    def restore():
        for n in (f'B_{side}_Clavicle', ua, fa, hd):
            rig.pose.bones[n].matrix_basis = ref_snapshot[n]
        bpy.context.view_layer.update()
    restore()
    S = W(rig, ua).translation.copy(); E0 = W(rig, fa).translation.copy(); W0 = W(rig, hd).translation.copy()
    T = Vector(wrist); u = (T - S).normalized()
    r = (W0 - S).normalized(); p0 = (E0 - S) - r * (E0 - S).dot(r)
    p0 = (r.rotation_difference(u) @ p0) if p0.length > 1e-6 else Vector((0, 0, -1))
    p0 = (p0 - u * p0.dot(u)).normalized()
    dn = Vector(direction).normalized()
    up = Vector((0, 0, 1)); rt = dn.cross(up).normalized() if abs(dn.dot(up)) < 0.99 else Vector((1, 0, 0))
    best = None
    phi_list = [fixed[0]] if fixed else list(phis)
    dev_list = [fixed[1]] if fixed else list(devs)
    for phi in phi_list:
        restore()
        pole = S + Quaternion(u, math.radians(phi)) @ p0
        solve(rig, side, T, pole=pole)
        for dp, dy in dev_list:
            d = Quaternion(up, math.radians(dy)) @ (Quaternion(rt, math.radians(dp)) @ dn)
            pr = prev['roll'] if prev else None
            R, roll, sw, tw = hand_for_axis(rig, side, axis_local, d, prev_roll=pr, k_twist=k_twist,
                                            k_cont=k_cont[1], twist_bias=twist_neutral)
            c = sw + k_twist * abs(tw - twist_neutral) + k_phi * abs(phi) + k_dev * math.hypot(dp, dy)
            if prev:
                c += k_cont[0] * abs(phi - prev['phi']) + k_cont[2] * math.hypot(dp - prev['dev'][0], dy - prev['dev'][1])
                c += k_cont[1] * abs((roll - prev['roll'] + 180) % 360 - 180)
            if best is None or c < best['cost']:
                best = {'cost': c, 'phi': phi, 'dev': (dp, dy), 'roll': roll, 'R': R, 'swing': sw, 'twist': tw, 'dir': d}
    restore()
    solve(rig, side, T, pole=S + Quaternion(u, math.radians(best['phi'])) @ p0)
    set_world(rig, hd, rot_world(W(rig, hd), best['R']))
    return best


def hand_rot(axis_local, direction, psi_deg, finger_local=Vector((0, 1, 0))):
    """Absolute hand orientation: grip axis along `direction`, fingers at angle psi about it, measured from world up
    projected perpendicular to the direction (psi = 0: fingers point up). Continuous across elbow choices."""
    d = Vector(direction).normalized(); up = Vector((0, 0, 1))
    u1 = up - d * up.dot(d)
    u1 = u1.normalized() if u1.length > 1e-6 else Vector((1, 0, 0))
    u2 = d.cross(u1)
    f = u1 * math.cos(math.radians(psi_deg)) + u2 * math.sin(math.radians(psi_deg))
    e1 = Vector(axis_local).normalized(); e2 = Vector(finger_local) - e1 * e1.dot(finger_local); e2.normalize()
    Bl = Matrix((e1, e2, e1.cross(e2))).transposed(); Bw = Matrix((d, f, d.cross(f))).transposed()
    return Bw @ Bl.transposed()


def arm_dp(rig, side, frames, axis_local, phis=range(-90, 91, 10), psis=range(0, 360, 5), devs=((0, 0),),
           k_twist=0.35, twist_neutral=30.0, k_phi=0.1, k_dev=0.5, k_dphi=0.6, k_dpsi=0.5, k_swing2=0.02):
    """Global (Viterbi) choice of elbow plane phi and hand roll psi over a clip. frames: list of dicts with 'snap'
    (matrix_basis of all bones, body pose with the arm still at its reference), 'wrist' (world) and 'dir' (world spear
    direction). Per frame and (phi, psi) the best spear deviation `dev` (pitch, yaw deg) is taken. Cost: wrist swing
    (+ k_swing2 swing^2 so large bends cost more) + k_twist |twist - neutral| + k_phi |phi| + k_dev |dev|; transitions:
    k_dphi |dphi| + k_dpsi |dpsi| (deg). Returns per frame (phi, psi, dev, swing, twist)."""
    import numpy as np
    ua, fa, hd = f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand'
    PH, PS = list(phis), list(psis)
    up = Vector((0, 0, 1))
    tables = []
    for fr in frames:
        for n, m in fr['snap'].items():
            rig.pose.bones[n].matrix_basis = m
        bpy.context.view_layer.update()
        S = W(rig, ua).translation.copy(); E0 = W(rig, fa).translation.copy(); W0 = W(rig, hd).translation.copy()
        T = Vector(fr['wrist']); u = (T - S).normalized()
        r = (W0 - S).normalized(); p0 = (E0 - S) - r * (E0 - S).dot(r)
        p0 = (r.rotation_difference(u) @ p0) if p0.length > 1e-6 else Vector((0, 0, -1))
        p0 = (p0 - u * p0.dot(u)).normalized()
        dn = Vector(fr['dir']).normalized(); rt = dn.cross(up).normalized()
        dirs = [(dv, (Quaternion(up, math.radians(dv[1])) @ (Quaternion(rt, math.radians(dv[0])) @ dn))) for dv in (fr.get('devs') or devs)]
        C = np.full((len(PH), len(PS)), 1e9); DV = np.zeros((len(PH), len(PS), 2)); SWT = np.zeros((len(PH), len(PS), 2))
        for a, phi in enumerate(PH):
            for n, m in fr['snap'].items():
                if n in (ua, fa, hd):
                    rig.pose.bones[n].matrix_basis = m
            bpy.context.view_layer.update()
            solve(rig, side, T, pole=S + Quaternion(u, math.radians(phi)) @ p0)
            Mf = W(rig, fa).to_3x3().normalized()
            rest_rel = (rig.data.bones[fa].matrix_local.to_3x3().inverted() @ rig.data.bones[hd].matrix_local.to_3x3()).inverted()
            for b, psi in enumerate(PS):
                for dv, d in dirs:
                    R = hand_rot(axis_local, d, psi)
                    rel = rest_rel @ (Mf.inverted() @ R)
                    sw, tw = split_swing_twist(rel.to_quaternion(), Vector((0, 1, 0)))
                    swd = math.degrees(sw.angle if sw.angle <= math.pi else 2 * math.pi - sw.angle); twd = math.degrees(tw)
                    c = swd + k_swing2 * swd * swd + k_twist * abs(twd - twist_neutral) + k_phi * abs(phi) + k_dev * math.hypot(*dv)
                    if c < C[a, b]:
                        C[a, b] = c; DV[a, b] = dv; SWT[a, b] = (swd, twd)
        tables.append((C, DV, SWT))
    nph, nps = len(PH), len(PS)
    dphi = np.abs(np.subtract.outer(np.array(PH, float), np.array(PH, float))) * k_dphi
    ps = np.array(PS, float); dps = np.abs((np.subtract.outer(ps, ps) + 180) % 360 - 180) * k_dpsi
    acc = tables[0][0].copy(); back = []
    for C, _, _ in tables[1:]:
        # min over previous phi' then previous psi' (separable L1 transition)
        m1 = np.min(acc[None, :, :] + dphi[:, :, None], axis=1); a1 = np.argmin(acc[None, :, :] + dphi[:, :, None], axis=1)
        m2 = np.min(m1[:, None, :] + dps[None, :, :], axis=2); a2 = np.argmin(m1[:, None, :] + dps[None, :, :], axis=2)
        back.append((a1, a2)); acc = m2 + C
    a, b = np.unravel_index(int(np.argmin(acc)), acc.shape); path = [(a, b)]
    for a1, a2 in reversed(back):
        bp = a2[a, b]; ap = a1[a, bp]; a, b = ap, bp; path.append((a, b))
    path.reverse()
    out = []
    for (a, b), (C, DV, SWT) in zip(path, tables):
        out.append({'phi': PH[a], 'psi': PS[b], 'dev': tuple(DV[a, b]), 'swing': SWT[a, b][0], 'twist': SWT[a, b][1]})
    return out


def apply_arm(rig, side, snap, wrist, axis_local, direction, phi, psi, dev=(0, 0)):
    """Pose the arm for a chosen (phi, psi, dev) on top of the body pose `snap`."""
    ua, fa, hd = f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand'
    for n, m in snap.items():
        rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update()
    S = W(rig, ua).translation.copy(); E0 = W(rig, fa).translation.copy(); W0 = W(rig, hd).translation.copy()
    T = Vector(wrist); u = (T - S).normalized()
    r = (W0 - S).normalized(); p0 = (E0 - S) - r * (E0 - S).dot(r)
    p0 = (r.rotation_difference(u) @ p0) if p0.length > 1e-6 else Vector((0, 0, -1))
    p0 = (p0 - u * p0.dot(u)).normalized()
    solve(rig, side, T, pole=S + Quaternion(u, math.radians(phi)) @ p0)
    up = Vector((0, 0, 1)); dn = Vector(direction).normalized(); rt = dn.cross(up).normalized()
    d = Quaternion(up, math.radians(dev[1])) @ (Quaternion(rt, math.radians(dev[0])) @ dn)
    set_world(rig, hd, rot_world(W(rig, hd), hand_rot(axis_local, d, psi)))
    return wrist_cost(rig, side, W(rig, hd).to_3x3().normalized())


def arm_options(rig,side,T,pole,degrees=range(-180,180,10)):
 import numpy as np
 un,fn,hn=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand')];U,F,H=[W(rig,n) for n in (un,fn,hn)];S=U.translation;E=F.translation;A=H.translation;a,b=(E-S).length,(A-E).length;d=T-S;dist=min(d.length,(a+b)*.965);u=d.normalized();v=(pole-u*pole.dot(u)).normalized();T=S+u*dist;ca=np.clip((a*a+dist*dist-b*b)/(2*a*dist),-1,1)
 ur,fr,hr=[rig.data.bones[n].matrix_local.to_3x3() for n in (un,fn,hn)];ru=(rig.data.bones[fn].head_local-rig.data.bones[un].head_local).normalized();rf=(rig.data.bones[hn].head_local-rig.data.bones[fn].head_local).normalized();lu=ur.inverted()@ru;lh=Vector((0,0,-1));lh=(lh-lu*lh.dot(lu)).normalized();B=Matrix((lu,lh.cross(lu),lh)).transposed();parent=rig.data.bones[un].parent;neutral=W(rig,parent.name).to_3x3()@parent.matrix_local.to_3x3().inverted()@ur
 options=[]
 for deg in degrees:
  vv=Quaternion(u,math.radians(deg))@v;K=S+a*(u*ca+vv*math.sqrt(max(0,1-ca*ca)));su=(K-S).normalized();sf=(T-K).normalized();normal=su.cross(sf).normalized();R=Matrix((su,normal.cross(su),normal)).transposed()@B.transposed();N=R@ur.inverted()@fr;rf_local=fr.inverted()@rf;Rf=(N@rf_local).rotation_difference(sf).to_matrix()@N;_,roll=split_swing_twist((neutral.inverted()@R).to_quaternion(),lu);rd=abs(math.degrees(roll));cost=max(0,rd-35)**2*20+rd*rd*.015+deg*deg*.003;options.append((cost,R,Rf,T,deg))
 return options
