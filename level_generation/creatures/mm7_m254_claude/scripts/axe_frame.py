"""The held weapon's prop frame (m414: the sword; m190: the axe) in B_R_Hand's local space (export_runtime.py's 'Sword' bone rule, bar1): origin at the solved
handle centre (work/grip_pose.json), +Y along the grip axis toward the head, +X = the knuckle direction (toward
B_R_Finger2) turned BLADE_ROLL degrees about the grip axis, +Z = X x Y. Shared by export_runtime.py and the review
stand-ins so they show the exported axe."""
import json, math, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLADE_ROLL = float(os.environ.get('BLADE_ROLL', '90'))


def hand_local(rig, roll_deg=None):
    G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
    ax = Vector(G['handle_axis_hand_local']).normalized(); c = Vector(G['handle_centre_hand_local'])
    Hm = rig.data.bones['B_R_Hand'].matrix_local
    kn = Hm.inverted() @ rig.data.bones['B_R_Finger2'].head_local
    side = kn - c; side = (side - ax * side.dot(ax)).normalized()
    r = math.radians(BLADE_ROLL if roll_deg is None else roll_deg)
    sx = (side * math.cos(r) + ax.cross(side) * math.sin(r)).normalized(); sz = sx.cross(ax)
    M = Matrix((sx, ax, sz)).transposed().to_4x4(); M.translation = c
    return M


def load_axe(scene):
    import bpy
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.endswith('Mesh')][:1]             # m414: 'SwordMesh'
    o = dst.objects[0]; scene.collection.objects.link(o)
    return o
