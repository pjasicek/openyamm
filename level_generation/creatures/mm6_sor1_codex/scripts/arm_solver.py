"""Shared staff/arm solving for the cleric rig (import inside Blender after the rig blend is open); adapted from
mm6_pmn2_claude/scripts/staff_rig.py (Meshy API bone names without a prefix, the staff in the LEFT fist).

An arm is solved onto a hand target given as a grip point and a staff axis: the hand's tunnel must lie on the staff
line with the tunnel's thumb end toward the staff head. Two-bone IK places the elbow toward a pole, the upper arm and
forearm take minimal swing from their rest relation to the parent (no added humeral twist), the forearm takes half of
the remaining hand twist (forearm_share), and the hand's roll about the staff axis is picked from 72 candidates for the least wrist
bend (+ continuity with the previous frame)."""
import bpy, math, json
import numpy as np
from mathutils import Vector, Quaternion

arm = bpy.data.objects['Rig']; scene = bpy.context.scene; AW = arm.matrix_world
mesh = bpy.data.objects['Body']; me = mesh.data
from pathlib import Path
G = json.loads((Path(__file__).resolve().parents[1]/'work/grip_pose.json').read_text())
STAFF_SIDE = 'B_R_'
Y = Vector((0,1,0))


def B(n):
    return arm.pose.bones[n]


def D(n):
    return arm.data.bones[n]


def rest3(n):
    return AW.to_3x3() @ D(n).matrix_local.to_3x3()


class Side:
    def __init__(self, side):
        self.s = side
        self.rest = {k: rest3(side + k) for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')}
        self.rel = {c: self.rest[p].inverted() @ self.rest[c] for p, c in (('Clavicle', 'UpperArm'), ('UpperArm', 'Forearm'), ('Forearm', 'Hand'))}
        self.l1 = (D(side + 'Forearm').head_local - D(side + 'UpperArm').head_local).length
        self.l2 = (D(side + 'Hand').head_local - D(side + 'Forearm').head_local).length
        # limb axes toward the child joint, in the bone's own frame: Meshy's bone tails are guesses, and moving the
        # wrist joints onto the hands (build_rig_cle.py) left the forearm Y axes 4-13 deg off the elbow -> wrist line
        self.uA = (self.rest['UpperArm'].inverted() @ (AW.to_3x3() @ (D(side + 'Forearm').head_local
                                                                  - D(side + 'UpperArm').head_local))).normalized()
        self.uF = (self.rest['Forearm'].inverted() @ (AW.to_3x3() @ (D(side + 'Hand').head_local
                                                                      - D(side + 'Forearm').head_local))).normalized()
        hand_rest = AW @ D(side + 'Hand').matrix_local
        self.axis_hand=Vector(G['handle_axis_hand_local']).normalized()
        self.grip_hand=Vector(G['handle_centre_hand_local'])

    def ik(self, S, W, pole):
        d = W - S; dist = min(d.length, (self.l1 + self.l2) * 0.999); dn = d.normalized()
        a = (self.l1 ** 2 + dist ** 2 - self.l2 ** 2) / (2 * dist); h = math.sqrt(max(self.l1 ** 2 - a * a, 0))
        pp = (pole - dn * pole.dot(dn)).normalized()
        return S + dn * a + pp * h, S + dn * dist

    def solve(self, G, a, pole, phi_prev=None, steps=72):
        """Best arm pose putting this hand's tunnel on the staff line through G (axis a, toward the head)."""
        S = AW @ B(self.s + 'UpperArm').head
        Rsh = (AW @ B(self.s + 'Clavicle').matrix).to_3x3()
        q0 = (self.rest['Hand'] @ self.axis_hand).rotation_difference(a).to_matrix()
        best = None
        for k in range(steps):
            phi = 2 * math.pi * k / steps
            Rh = Quaternion(a, phi).to_matrix() @ q0 @ self.rest['Hand']
            W = G - Rh @ self.grip_hand
            E, W2 = self.ik(S, W, pole)
            Ra = Rsh @ self.rel['UpperArm']; Ra = (Ra @ self.uA).rotation_difference((E - S).normalized()).to_matrix() @ Ra
            Rf = Ra @ self.rel['Forearm']; Rf = (Rf @ self.uF).rotation_difference((W2 - E).normalized()).to_matrix() @ Rf
            q = ((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion()
            tw0 = swing_twist_deg(q, Y)[1]
            Rf = Quaternion((Rf @ self.uF).normalized(), math.radians(forearm_share(tw0))).to_matrix() @ Rf
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
        S = AW @ B(self.s + 'UpperArm').head
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
        S = AW @ B(self.s + 'UpperArm').head
        Rsh = (AW @ B(self.s + 'Clavicle').matrix).to_3x3()
        W = G - Rh @ self.grip_hand
        E, W2 = self.ik(S, W, pole)
        Ra = Rsh @ self.rel['UpperArm']; Ra = (Ra @ self.uA).rotation_difference((E - S).normalized()).to_matrix() @ Ra
        Rf = Ra @ self.rel['Forearm']; Rf = (Rf @ self.uF).rotation_difference((W2 - E).normalized()).to_matrix() @ Rf
        tw0 = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)[1]
        Rf = Quaternion((Rf @ self.uF).normalized(), math.radians(forearm_share(tw0))).to_matrix() @ Rf
        sw, tw = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)
        return dict(cost=sw + 0.8 * abs(tw), phi=None, Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2, sw=sw, tw=tw, miss=(W - W2).length)

    def hinge_local(self):
        """Elbow hinge axis in the upper arm's rest frame (from the slight rest bend of the A-pose)."""
        ua = self.rest['UpperArm'] @ self.uA; fa = self.rest['Forearm'] @ self.uF
        return (self.rest['UpperArm'].inverted() @ ua.cross(fa)).normalized()

    def pose_anatomical(self, G, Rh, pole, prev_tw=None):
        """Arm pose for hand rotation Rh at grip G with anatomical twist: the upper arm rolls so its elbow hinge is normal
        to the shoulder-elbow-wrist plane, the forearm bends about that hinge, then takes the remaining hand twist
        (unwrapped toward prev_tw for continuity) up to +-90 deg; the wrist keeps the rest."""
        S = AW @ B(self.s + 'UpperArm').head
        Rsh = (AW @ B(self.s + 'Clavicle').matrix).to_3x3()
        W = G - Rh @ self.grip_hand
        E, W2 = self.ik(S, W, pole)
        u = (E - S).normalized(); f = (W2 - E).normalized()
        Ra = Rsh @ self.rel['UpperArm']; Ra = (Ra @ self.uA).rotation_difference(u).to_matrix() @ Ra
        n = u.cross(f)
        if n.length > 1e-4:                                 # roll the upper arm so its hinge lies along n
            h = (Ra @ self.hinge_local()); h = (h - u * h.dot(u)).normalized(); n = n.normalized()
            ang = math.atan2(h.cross(n).dot(u), h.dot(n))
            Ra = Quaternion(u, ang).to_matrix() @ Ra
        Rf = Ra @ self.rel['Forearm']; Rf = (Rf @ self.uF).rotation_difference(f).to_matrix() @ Rf
        tw0 = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)[1]
        if prev_tw is not None:
            while tw0 - prev_tw > 180: tw0 -= 360
            while tw0 - prev_tw < -180: tw0 += 360
        ft = max(-85.0, min(85.0, tw0))
        Rf = Quaternion((Rf @ self.uF).normalized(), math.radians(ft)).to_matrix() @ Rf
        sw, tw = swing_twist_deg(((Rf @ self.rel['Hand']).inverted() @ Rh).to_quaternion(), Y)
        return dict(cost=sw + 0.8 * abs(tw), phi=None, Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2, sw=sw, tw=tw,
                    miss=(W - W2).length, tw0=tw0, forearm_twist=ft)

    def apply(self, r, frame=None):
        """Set the arm pose (detached rig); key its rotations at frame only when frame is given."""
        for bn, R3, head in (('UpperArm', r['Ra'], r['S']), ('Forearm', r['Rf'], r['E']), ('Hand', r['Rh'], r['W'])):
            pb = B(self.s + bn); pb.rotation_mode = 'QUATERNION'
            M = R3.to_4x4(); M.translation = head
            pb.matrix = AW.inverted() @ M
            bpy.context.view_layer.update()
            if frame is not None:
                pb.keyframe_insert('rotation_quaternion', frame=frame)


def forearm_share(tw0):
    """The forearm's part of the hand's twist (deg): 70 %, at most 85 deg (the playback gate allows 45 deg of wrist
    twist and 90 of forearm twist; half-and-half left 46-78 deg at the wrist)."""
    return max(-85.0, min(85.0, 0.7 * tw0))


def swing_twist_deg(q, axis):
    p = Vector((q.x, q.y, q.z)).project(axis)
    t = Quaternion((q.w, p.x, p.y, p.z)); t.normalize(); s = q @ t.inverted()
    tw = math.degrees(2 * math.atan2(p.length, q.w)) * (1 if p.dot(axis) >= 0 else -1)
    return math.degrees(s.angle), (tw + 180) % 360 - 180

