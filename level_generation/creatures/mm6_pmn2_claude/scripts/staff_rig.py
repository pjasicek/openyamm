"""Shared staff/arm solving for the pmn2 rig (import inside Blender after the rig blend is open).

An arm is solved onto a hand target given as a grip point and a staff axis: the hand's tunnel must lie on the staff
line with the tunnel's thumb end toward the staff head. Two-bone IK places the elbow toward a pole, the upper arm and
forearm take minimal swing from their rest relation to the parent (no added humeral twist), the forearm takes half of
the remaining hand twist, and the hand's roll about the staff axis is picked from 72 candidates for the least wrist
bend (+ continuity with the previous frame)."""
import bpy, math, json
import numpy as np
from mathutils import Vector, Quaternion

arm = bpy.data.objects['Mage_Rig']; scene = bpy.context.scene; AW = arm.matrix_world
mesh = bpy.data.objects['Mage']; me = mesh.data
ST = json.loads(scene['pmn2_staff']); L = ST['length']
GRIP_FROM_FOOT = L * 0.71                                  # right grip, measured from the staff foot
Y = Vector((0, 1, 0))


def B(n):
    return arm.pose.bones[n if n.startswith('Staff') else 'mixamorig:' + n]


def D(n):
    return arm.data.bones[n if n.startswith('Staff') else 'mixamorig:' + n]


def rest3(n):
    return AW.to_3x3() @ D(n).matrix_local.to_3x3()


class Side:
    def __init__(self, side):
        self.s = side
        self.rest = {k: rest3(side + k) for k in ('Shoulder', 'Arm', 'ForeArm', 'Hand')}
        self.rel = {c: self.rest[p].inverted() @ self.rest[c] for p, c in (('Shoulder', 'Arm'), ('Arm', 'ForeArm'), ('ForeArm', 'Hand'))}
        self.l1 = (D(side + 'ForeArm').head_local - D(side + 'Arm').head_local).length
        self.l2 = (D(side + 'Hand').head_local - D(side + 'ForeArm').head_local).length
        hand_rest = AW @ D(side + 'Hand').matrix_local
        if side == 'Right':
            self.axis_hand = self.rest['Hand'].inverted() @ (rest3('Staff') @ Y)
            self.grip_hand = self.rest['Hand'].inverted() @ (AW @ D('Staff').head_local - hand_rest.translation)
        else:
            lt = json.loads(scene['pmn2_left_tunnel'])
            self.axis_hand = Vector(lt['axis_hand']).normalized()
            self.grip_hand = self.rest['Hand'].inverted() @ ((hand_rest @ Vector(lt['centre_hand'])) - hand_rest.translation)

    def ik(self, S, W, pole):
        d = W - S; dist = min(d.length, (self.l1 + self.l2) * 0.999); dn = d.normalized()
        a = (self.l1 ** 2 + dist ** 2 - self.l2 ** 2) / (2 * dist); h = math.sqrt(max(self.l1 ** 2 - a * a, 0))
        pp = (pole - dn * pole.dot(dn)).normalized()
        return S + dn * a + pp * h, S + dn * dist

    def solve(self, G, a, pole, phi_prev=None, steps=72):
        """Best arm pose putting this hand's tunnel on the staff line through G (axis a, toward the head)."""
        S = AW @ B(self.s + 'Arm').head
        Rsh = (AW @ B(self.s + 'Shoulder').matrix).to_3x3()
        q0 = (self.rest['Hand'] @ self.axis_hand).rotation_difference(a).to_matrix()
        best = None
        for k in range(steps):
            phi = 2 * math.pi * k / steps
            Rh = Quaternion(a, phi).to_matrix() @ q0 @ self.rest['Hand']
            W = G - Rh @ self.grip_hand
            E, W2 = self.ik(S, W, pole)
            Ra = Rsh @ self.rel['Arm']; Ra = (Ra @ Y).rotation_difference((E - S).normalized()).to_matrix() @ Ra
            Rf = Ra @ self.rel['ForeArm']; Rf = (Rf @ Y).rotation_difference((W2 - E).normalized()).to_matrix() @ Rf
            q = ((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion()
            tw0 = swing_twist_deg(q, Y)[1]
            Rf = Quaternion((Rf @ Y).normalized(), math.radians(tw0 * 0.5)).to_matrix() @ Rf
            sw, tw = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)
            cost = sw + 0.8 * abs(tw) + 0.25 * abs(tw0)
            if phi_prev is not None:
                cost += 0.3 * math.degrees(abs((phi - phi_prev + math.pi) % (2 * math.pi) - math.pi))
            if best is None or cost < best['cost']:
                best = dict(cost=cost, phi=phi, Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2, sw=sw, tw=tw, miss=(W - W2).length)
        return best

    def search(self, cands, pole0, phi_prev=None, extra_cost=None, steps=36):
        """Best solve over candidate (grip point, staff axis, tag) and elbow poles rotated about the shoulder-wrist
        line by -60..60 deg. extra_cost(cand) adds e.g. staff clearance or continuity penalties."""
        S = AW @ B(self.s + 'Arm').head
        best = None
        for G, a, tag in cands:
            pen = extra_cost((G, a, tag)) if extra_cost else 0.0
            if best is not None and pen >= best['cost']:
                continue
            axis = (G - S).normalized()
            for ang in (-60, -30, 0, 30, 60):
                pole = Quaternion(axis, math.radians(ang)) @ pole0
                r = self.solve(G, a, pole, phi_prev, steps)
                r['cost'] += pen + 0.05 * abs(ang); r['tag'] = tag; r['G'] = G; r['a'] = a
                if best is None or r['cost'] < best['cost']:
                    best = r
        return best

    def pose_for(self, G, Rh, pole):
        """Arm pose for a given hand rotation Rh and grip point G (no roll search): wrist from the grip offset, two-bone
        IK toward pole, minimal-swing upper arm/forearm, forearm takes half of the hand twist."""
        S = AW @ B(self.s + 'Arm').head
        Rsh = (AW @ B(self.s + 'Shoulder').matrix).to_3x3()
        W = G - Rh @ self.grip_hand
        E, W2 = self.ik(S, W, pole)
        Ra = Rsh @ self.rel['Arm']; Ra = (Ra @ Y).rotation_difference((E - S).normalized()).to_matrix() @ Ra
        Rf = Ra @ self.rel['ForeArm']; Rf = (Rf @ Y).rotation_difference((W2 - E).normalized()).to_matrix() @ Rf
        tw0 = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)[1]
        Rf = Quaternion((Rf @ Y).normalized(), math.radians(tw0 * 0.5)).to_matrix() @ Rf
        sw, tw = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)
        return dict(cost=sw + 0.8 * abs(tw), phi=None, Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2, sw=sw, tw=tw, miss=(W - W2).length)

    def hinge_local(self):
        """Elbow hinge axis in the upper arm's rest frame (from the slight rest bend of the A-pose)."""
        ua = self.rest['Arm'] @ Y; fa = self.rest['ForeArm'] @ Y
        return (self.rest['Arm'].inverted() @ ua.cross(fa)).normalized()

    def pose_anatomical(self, G, Rh, pole, prev_tw=None):
        """Arm pose for hand rotation Rh at grip G with anatomical twist: the upper arm rolls so its elbow hinge is normal
        to the shoulder-elbow-wrist plane, the forearm bends about that hinge, then takes the remaining hand twist
        (unwrapped toward prev_tw for continuity) up to +-90 deg; the wrist keeps the rest."""
        S = AW @ B(self.s + 'Arm').head
        Rsh = (AW @ B(self.s + 'Shoulder').matrix).to_3x3()
        W = G - Rh @ self.grip_hand
        E, W2 = self.ik(S, W, pole)
        u = (E - S).normalized(); f = (W2 - E).normalized()
        Ra = Rsh @ self.rel['Arm']; Ra = (Ra @ Y).rotation_difference(u).to_matrix() @ Ra
        n = u.cross(f)
        if n.length > 1e-4:                                 # roll the upper arm so its hinge lies along n
            h = (Ra @ self.hinge_local()); h = (h - u * h.dot(u)).normalized(); n = n.normalized()
            ang = math.atan2(h.cross(n).dot(u), h.dot(n))
            Ra = Quaternion(u, ang).to_matrix() @ Ra
        Rf = Ra @ self.rel['ForeArm']; Rf = (Rf @ Y).rotation_difference(f).to_matrix() @ Rf
        tw0 = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)[1]
        if prev_tw is not None:
            while tw0 - prev_tw > 180: tw0 -= 360
            while tw0 - prev_tw < -180: tw0 += 360
        ft = max(-90.0, min(90.0, tw0))
        Rf = Quaternion((Rf @ Y).normalized(), math.radians(ft)).to_matrix() @ Rf
        sw, tw = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)
        return dict(cost=sw + 0.8 * abs(tw), phi=None, Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2, sw=sw, tw=tw,
                    miss=(W - W2).length, tw0=tw0, forearm_twist=ft)

    def apply(self, r, frame):
        for bn, R3, head in (('Arm', r['Ra'], r['S']), ('ForeArm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
            pb = B(self.s + bn); pb.rotation_mode = 'QUATERNION'
            M = R3.to_4x4(); M.translation = head
            pb.matrix = AW.inverted() @ M
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=frame)


def swing_twist_deg(q, axis):
    p = Vector((q.x, q.y, q.z)).project(axis)
    t = Quaternion((q.w, p.x, p.y, p.z)); t.normalize(); s = q @ t.inverted()
    tw = math.degrees(2 * math.atan2(p.length, q.w)) * (1 if p.dot(axis) >= 0 else -1)
    return math.degrees(s.angle), (tw + 180) % 360 - 180


def body_frame():
    lx = AW @ B('LeftUpLeg').head - AW @ B('RightUpLeg').head; lx.z = 0; lx.normalize()
    F = lx.cross(Vector((0, 0, 1))).normalized()
    return AW @ B('Hips').head, F, -lx                    # hips, forward, right


def set_action(name):
    act = bpy.data.actions[name]; arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    return act, tuple(int(round(x)) for x in act.frame_range)


PARTS = json.loads(scene['pmn2_parts'])
_gname = {g.index: g.name for g in mesh.vertex_groups}
_dom = [_gname.get(max(v.groups, key=lambda g: g.weight).group) if v.groups else None for v in me.vertices]


def body_points(skip=('mixamorig:RightHand', 'mixamorig:RightForeArm')):
    idx = np.array([i for i, g in enumerate(_dom) if g not in skip])
    dg = bpy.context.evaluated_depsgraph_get(); em = mesh.evaluated_get(dg).to_mesh()
    P = np.array([tuple(mesh.matrix_world @ em.vertices[i].co) for i in idx]); mesh.evaluated_get(dg).to_mesh_clear()
    return P


def shaft_clearance(P, G, a, below_grip=GRIP_FROM_FOOT - 0.06, above_grip=0.0, radius=0.024):
    """Smallest body-vertex distance to the shaft surface between (grip - below_grip) and (grip + above_grip)."""
    base = np.array(G - a * below_grip); ax = np.array(a); rel = P - base; t = rel @ ax
    m = (t > 0) & (t < below_grip + above_grip)
    if not m.any():
        return 1.0
    return float((np.linalg.norm(rel[m] - np.outer(t[m], ax), axis=1) - radius).min())


def _set_world(name, R3, head, frame):
    pb = B(name); pb.rotation_mode = 'QUATERNION'
    M = R3.to_4x4(); M.translation = head; pb.matrix = AW.inverted() @ M
    bpy.context.view_layer.update()
    if frame is not None:
        pb.keyframe_insert('rotation_quaternion', frame=frame)


def leg_ik(side, foot_world, knee_hint, frame):
    """Two-bone leg IK: foot to foot_world (4x4, its rotation kept), knee toward knee_hint (world direction).
    Returns how far the foot misses (m) when the target is out of reach."""
    l1 = (D(side + 'UpLeg').head_local - D(side + 'Leg').head_local).length
    l2 = (D(side + 'Leg').head_local - D(side + 'Foot').head_local).length
    up, lo = B(side + 'UpLeg'), B(side + 'Leg')
    H = AW @ up.head; A = foot_world.translation
    d = A - H; dist = min(d.length, (l1 + l2) * 0.999); dn = d.normalized()
    a = (l1 * l1 + dist * dist - l2 * l2) / (2 * dist); h = math.sqrt(max(l1 * l1 - a * a, 0))
    pole = (knee_hint - dn * knee_hint.dot(dn)).normalized()
    K = H + dn * a + pole * h; A2 = H + dn * dist
    Ru = (AW @ up.matrix).to_3x3(); Ru = (Ru @ Y).rotation_difference((K - H).normalized()).to_matrix() @ Ru
    _set_world(side + 'UpLeg', Ru, H, frame)
    Rl = (AW @ lo.matrix).to_3x3(); Rl = (Rl @ Y).rotation_difference((A2 - K).normalized()).to_matrix() @ Rl
    _set_world(side + 'Leg', Rl, K, frame)
    _set_world(side + 'Foot', foot_world.to_3x3(), A2, frame)
    return (A2 - A).length


def rotate_bone_world(name, axis, angle_deg):
    """Rotate a pose bone about a world axis through its head (adds to the current pose)."""
    pb = B(name); M = AW @ pb.matrix; piv = M.translation.copy()
    from mathutils import Matrix
    M = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(angle_deg), 4, axis.normalized()) @ Matrix.Translation(-piv) @ M
    pb.matrix = AW.inverted() @ M
    bpy.context.view_layer.update()


def sample_pose(action, frame):
    set_action(action); scene.frame_set(frame)
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in arm.pose.bones}


def set_pose(pose):
    for n, (q, loc) in pose.items():
        pb = arm.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = loc
    bpy.context.view_layer.update()


def key_all(frame):
    for pb in arm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=frame); pb.keyframe_insert('location', frame=frame)


_part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', _part)
_HEAD_POLYS = [p.index for p in me.polygons if PARTS[_part[p.index]] in ('Head', 'EyeL', 'EyeR')]   # face/skull, not hair
_ARM_VERTS = np.array([i for i, g in enumerate(_dom) if g and any(k in g for k in ('RightArm', 'RightForeArm', 'RightHand',
                                                                                   'LeftArm', 'LeftForeArm', 'LeftHand'))])


def head_penetration():
    """Arm vertices inside the deformed head/eye shells (face and skull; arm under the long hair at the shoulders is
    hidden and not counted): (count, deepest mm). Inside = the nearest head surface point's normal faces away from the
    vertex, within 8 cm (the head shell is open only at the neck)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); em = mesh.evaluated_get(dg).to_mesh()
    V = [mesh.matrix_world @ v.co for v in em.vertices]
    tree = BVHTree.FromPolygons(V, [tuple(em.polygons[i].vertices) for i in _HEAD_POLYS])
    neck_z = min(V[i].z for i in em.polygons[_HEAD_POLYS[0]].vertices)
    n, deep = 0, 0.0
    for i in _ARM_VERTS:
        loc, nor, idx, dist = tree.find_nearest(V[i], 0.08)
        if loc is not None and (V[i] - loc).dot(nor) < 0:
            n += 1; deep = max(deep, dist)
    mesh.evaluated_get(dg).to_mesh_clear()
    return n, round(deep * 1000, 1)


def fix_quaternion_signs(action):
    """Make each bone's rotation_quaternion keys sign-continuous (q and -q are the same rotation, but interpolating
    between keys of opposite sign spins the bone the long way round). Returns the number of keys negated."""
    curves = {}
    fcs = list(getattr(action, 'fcurves', []))
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        if fc.data_path.endswith('rotation_quaternion'):
            curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    flipped = 0
    for path, comps in curves.items():
        if len(comps) != 4:
            continue
        keys = [comps[i].keyframe_points for i in range(4)]
        n = min(len(k) for k in keys)
        prev = None
        for j in range(n):
            q = [keys[i][j].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                for i in range(4):
                    kp = keys[i][j]; kp.co[1] = -kp.co[1]
                    kp.handle_left[1] = -kp.handle_left[1]; kp.handle_right[1] = -kp.handle_right[1]
                q = [-x for x in q]; flipped += 1
            prev = q
        for i in range(4):
            comps[i].update()
    return flipped
