"""Helpers shared by author_clips.py and author_death.py (import after staff_rig, inside Blender)."""
import math
from mathutils import Vector, Quaternion
import staff_rig as sr

AW = sr.AW


def V(*x):
    return Vector(x)


def catmull(keys, name, f, default):
    """Catmull-Rom through the keys' values (keys without the field use default) at frame f."""
    ks = [(k['f'], k.get(name, default)) for k in keys]
    for i in range(len(ks) - 1):
        f0, p1 = ks[i]; f1, p2 = ks[i + 1]
        if f0 <= f <= f1:
            p0 = ks[i - 1][1] if i > 0 else p1
            p3 = ks[i + 2][1] if i + 2 < len(ks) else p2
            t = (f - f0) / (f1 - f0)
            if isinstance(p1, tuple):
                p0, p1, p2, p3 = (Vector(x) for x in (p0, p1, p2, p3))
            v = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                       + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)
            return v
    return Vector(ks[-1][1]) if isinstance(ks[-1][1], tuple) else ks[-1][1]


def free_arm(side, W, pole, frame=None):
    """Two-bone IK to wrist W, upper arm rolled so the elbow hinges in the shoulder-elbow-wrist plane, hand straight
    on the forearm (no prop to hold)."""
    S = AW @ sr.B(side.s + 'Arm').head
    Rsh = (AW @ sr.B(side.s + 'Shoulder').matrix).to_3x3()
    E, W2 = side.ik(S, W, pole)
    u = (E - S).normalized(); fdir = (W2 - E).normalized()
    Ra = Rsh @ side.rel['Arm']; Ra = (Ra @ side.uA).rotation_difference(u).to_matrix() @ Ra
    n = u.cross(fdir)
    if n.length > 1e-4:
        h = Ra @ side.hinge_local(); h = (h - u * h.dot(u)).normalized(); n = n.normalized()
        Ra = Quaternion(u, math.atan2(h.cross(n).dot(u), h.dot(n))).to_matrix() @ Ra
    Rf = Ra @ side.rel['ForeArm']; Rf = (Rf @ side.uF).rotation_difference(fdir).to_matrix() @ Rf
    Rh = Rf @ side.rel['Hand']
    side.apply(dict(Ra=Ra, Rf=Rf, Rh=Rh, S=S, E=E, W=W2), frame)
    return (W - W2).length


def staff_on_floor(G, a, clear=0.02):
    """Tilt the staff (keeping its horizontal heading) so its foot stays on or above the floor as the hand drops."""
    zmax = (G.z - clear) / sr.GRIP_FROM_FOOT
    if a.z <= zmax:
        return a
    h = Vector((a.x, a.y, 0))
    if h.length < 1e-4:
        h = Vector((1, 0, 0))
    h.normalize(); z = max(-1.0, min(1.0, zmax))
    return (h * math.sqrt(1 - z * z) + Vector((0, 0, z))).normalized()
