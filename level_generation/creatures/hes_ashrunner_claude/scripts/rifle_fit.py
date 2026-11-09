"""hgd: the rifle in the right fist, held as a pistol grip (user review 2026-10-22: the first fit followed the set's
right hand, whose finger curl runs sideways across the body, and rolled the rifle 90 deg: the grip went sideways into
the body and the power-cell window faced up). Prop frame in B_R_Hand rest-local coordinates (the hand continues the
forearm, build_rig.py HAND_FROM_FOREARM): origin = the right grip tunnel's centre, Z = the tunnel axis toward the thumb
(up the pistol grip to the bore), Y = the hand's axis (wrist -> knuckles) made perpendicular to Z (the barrel along the
knuckles), X = Y x Z (the gun's right side). The handguard (left fist) sits at Y = HG_Y, Z = HG_Z in this frame
(make_rifle.py). Writes work/rifle_frame.json. Args: -- <blend>"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HG_Y, HG_Z = float(os.environ.get('HG_Y', '0.35')), float(os.environ.get('HG_Z', '0.064'))
rig = bpy.data.objects['Rig']
GR = json.load(open(os.path.join(HERE, 'work', 'grip_pose_R.json')))
c = Vector(GR['handle_centre_hand_local']); g = Vector(GR['handle_axis_hand_local']).normalized()
H = rig.data.bones['B_R_Hand'].matrix_local
if (H.to_3x3() @ g).dot(Vector((0, -1, 0))) < 0:      # A-pose fists: palms toward the thighs, thumbs forward (-Y)
    g = -g
f = Vector((0, 1, 0)); y = (f - g * f.dot(g)).normalized(); x = y.cross(g)
Hr = Matrix((x, y, g)).transposed().to_4x4(); Hr.translation = c
out = {'rifle_in_hand': [list(r) for r in Hr], 'left_centre_rifle': [0.0, HG_Y, HG_Z], 'left_axis_rifle': [0.0, 1.0, 0.0],
       'grip_to_hand_axis_deg': math.degrees(g.angle(f))}
json.dump(out, open(os.path.join(HERE, 'work', 'rifle_frame.json'), 'w'), indent=1)
print('RIFLEFIT pistol grip: tunnel axis vs the hand axis deg', round(out['grip_to_hand_axis_deg'], 1), 'handguard', HG_Y, HG_Z)
