"""Hand posing helpers (run inside Blender): finger flexion about each finger's curl-plane axis (rig_info.json),
spread (abduction about the palm normal) and the lip lids. Angles in degrees; + flex = curl toward the palm."""
import bpy, math, json, os
from mathutils import Matrix, Vector
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO = json.load(open(os.path.join(HERE, 'work', 'rig_info.json')))
SPREAD_SIGN = {'Thumb': 1.0, 'Index': 0.6, 'Middle': 0.0, 'Ring': -0.6, 'Pinky': -1.0}


def reset(rig):
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0)
        b.location = (0, 0, 0); b.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def rot_about(rig, name, axis_world, deg):
    pb = rig.pose.bones[name]
    head = pb.head.copy()                     # armature at identity object transform
    R = Matrix.Translation(head) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis_world)) @ Matrix.Translation(-head)
    pb.matrix = R @ pb.matrix
    bpy.context.view_layer.update()


def hand(rig, flex, spread=0.0, lips=0.0):
    """flex: {finger: (a1, a2, a3)} or one triple for all; spread: degrees of abduction (+ fans out);
    lips: opening angle of the lids (0 closed). Bones posed proximal to distal in the rest frame of each finger
    (the axis is carried by the parent's rotation)."""
    for f in FINGERS:
        ang = flex[f] if isinstance(flex, dict) else flex
        axis = Vector(INFO['axes'][f])
        sp = spread * SPREAD_SIGN[f]
        R_acc = Matrix.Identity(3)
        for i in range(3):
            name = f'{f}_{i + 1}'
            if i == 0 and sp:
                rot_about(rig, name, Vector(INFO['n']), sp)
                R_acc = Matrix.Rotation(math.radians(sp), 3, Vector(INFO['n']))
            ax = R_acc @ axis
            rot_about(rig, name, ax, ang[i])
            R_acc = Matrix.Rotation(math.radians(ang[i]), 3, ax) @ R_acc
    if lips:
        U = Vector(INFO['U'])
        rot_about(rig, 'LipUpper', U, -lips)
        rot_about(rig, 'LipLower', U, lips)
