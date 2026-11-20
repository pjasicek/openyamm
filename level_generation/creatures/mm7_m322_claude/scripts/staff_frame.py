"""The staff's prop frame (m322: LEFT hand, PROP_SIDE) in B_<side>_Hand's local space (export_runtime.py's 'Sword' bone rule, bar1; after
mm7_m190_claude/scripts/axe_frame.py): origin at the solved handle centre (work/grip_pose.json), +Y along the grip axis
toward the head (out of the thumb side; CLUB_FLIP=1 reverses it - tried 2026-10-20: the club then points back, not
down), +X = the knuckle direction (toward B_R_Finger2) turned ROLL degrees about the grip axis, +Z = X x Y.
The club is nearly round, so the roll only turns its texture. Shared by export_runtime.py and the review stand-ins."""
import json, math, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDE = 'L'                                             # m322: the staff is in her LEFT hand
SUF = '' if SIDE == 'R' else '_' + SIDE
ROLL = float(os.environ.get('CLUB_ROLL', '90'))
FLIP = os.environ.get('CLUB_FLIP', '0') == '1'


def hand_local(rig, roll_deg=None):
    G = json.load(open(os.path.join(HERE, 'work', f'grip_pose{SUF}.json')))
    ax = Vector(G['handle_axis_hand_local']).normalized(); c = Vector(G['handle_centre_hand_local'])
    if FLIP:
        ax = -ax
    Hm = rig.data.bones[f'B_{SIDE}_Hand'].matrix_local
    kn = Hm.inverted() @ rig.data.bones[f'B_{SIDE}_Finger2'].head_local
    side = kn - c; side = (side - ax * side.dot(ax)).normalized()
    r = math.radians(ROLL if roll_deg is None else roll_deg)
    sx = (side * math.cos(r) + ax.cross(side) * math.sin(r)).normalized(); sz = sx.cross(ax)
    M = Matrix((sx, ax, sz)).transposed().to_4x4(); M.translation = c
    return M


def load_staff(scene):
    import bpy
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
        dst.objects = ['StaffMesh']
    o = dst.objects[0]; scene.collection.objects.link(o)
    return o
