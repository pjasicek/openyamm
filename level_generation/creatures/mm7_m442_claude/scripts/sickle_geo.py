"""Sickle sample points in B_R_Hand-local space (gob2 lesson: a curved blade must be tested on its real shape, not on a
straight chord). The prop frame is the one export_runtime.py gives the Sword bone: origin at the solved handle centre
(work/grip_pose.json), +Y along the grip axis toward the blade, +X = the knuckle direction (B_R_Finger2 head,
perpendicular to the axis) turned BLADE_ROLL about the axis. Points: the blade outline from
textures/props/sickle_shape.json (prop metres), resampled to ~N points, blade only (y above the handle top)."""
import json, math, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLL_DEG = float(os.environ.get('BLADE_ROLL', '90'))


def frame(rig, G, roll_deg=None):
    roll = math.radians(ROLL_DEG if roll_deg is None else roll_deg)
    Hm = rig.data.bones['B_R_Hand'].matrix_local
    c = Vector(G['handle_centre_hand_local']); ax = Vector(G['handle_axis_hand_local']).normalized()
    kn = Hm.inverted() @ rig.data.bones['B_R_Finger2'].head_local
    side = kn - c; side = (side - ax * side.dot(ax)).normalized()
    sx = (side * math.cos(roll) + ax.cross(side) * math.sin(roll)).normalized()
    return c, ax, sx


def local_points(rig, G, n=48, roll_deg=None):
    S = json.load(open(os.path.join(HERE, 'textures', 'props', 'sickle_shape.json')))
    O = np.array(S['outline']); O = O[O[:, 1] > S['handle']['y_top']]
    O = O[np.linspace(0, len(O) - 1, min(n, len(O))).astype(int)]
    c, ax, sx = frame(rig, G, roll_deg)
    return [c + ax * float(y) + sx * float(x) for x, y in O]
