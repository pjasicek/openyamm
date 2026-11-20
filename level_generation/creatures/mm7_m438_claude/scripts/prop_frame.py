"""The held prop's frame in the carrying hand's local space (m438: the severed forearm in the LEFT fist; after
mm7_m190_claude's axe_frame.py, bar1's 'Sword' bone rule): origin at the solved handle centre (work/grip_pose_L.json),
+Y along the grip axis (out of the thumb side, toward the elbow cut = the club head), +X = the knuckle direction
(toward B_L_Finger2) turned PROP_ROLL degrees about the grip axis, +Z = X x Y. The prop's own +X (toward the
severed thumb) lies on this +X. Shared by export_runtime.py, the clearance step and the review stand-ins."""
import json, math, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDE = os.environ.get('PROP_SIDE', 'L')
PROP_ROLL = float(os.environ.get('PROP_ROLL', '0'))
PROP = 'ForearmMesh'


def grip():
    return json.load(open(os.path.join(HERE, 'work', 'grip_pose%s.json' % ('' if SIDE == 'R' else '_' + SIDE))))


def hand_local(rig, roll_deg=None):
    G = grip()
    ax = Vector(G['handle_axis_hand_local']).normalized(); c = Vector(G['handle_centre_hand_local'])
    Hm = rig.data.bones[f'B_{SIDE}_Hand'].matrix_local
    kn = Hm.inverted() @ rig.data.bones[f'B_{SIDE}_Finger2'].head_local
    side = kn - c; side = (side - ax * side.dot(ax)).normalized()
    r = math.radians(PROP_ROLL if roll_deg is None else roll_deg)
    sx = (side * math.cos(r) + ax.cross(side) * math.sin(r)).normalized(); sz = sx.cross(ax)
    M = Matrix((sx, ax, sz)).transposed().to_4x4(); M.translation = c
    return M


def load_prop(scene):
    import bpy
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
        dst.objects = [PROP]
    o = dst.objects[0]; scene.collection.objects.link(o)
    return o
