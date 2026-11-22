"""Extreme poses on work/rig_v1.blend before animating: rest, stride (left legs forward, right back), crouch (front
low, elbows and hocks bent), snarl (jaw open 38 degrees, head up), swipe (left foreleg raised forward), roll onto the
right side, head and tail turn. Writes review/stress_<pose>_<cam>.png and review/stress_sheet.png."""
import bpy, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig = bpy.data.objects['Saber_Rig']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
CAMS = {'quarter': ((2.6, -3.4, 1.9), (0, -0.2, 0.6)), 'side': ((4.0, 0, 0.7), (0, 0, 0.6))}
shots = []


def shoot(name, cams=CAMS, size=2.8):
    for c, (loc, tgt) in cams.items():
        p = os.path.join(HERE, 'review', f'stress_{name}_{c}.png'); shots.append(p)
        C.render(loc, tgt, size, p, res=(600, 480))


P.reset(rig); shoot('rest')
P.reset(rig)
P.rotate_world(rig, 'UpperArm_L', X, -30); P.rotate_world(rig, 'ForeArm_L', X, 15)
P.rotate_world(rig, 'UpperArm_R', X, 25); P.rotate_world(rig, 'FrontPaw_R', X, 40)
P.rotate_world(rig, 'Thigh_L', X, -25); P.rotate_world(rig, 'Thigh_R', X, 30); P.rotate_world(rig, 'Hock_R', X, -30)
P.rotate_world(rig, 'Scapula_L', X, -12)
shoot('stride')
P.reset(rig)
P.rotate_world(rig, 'Body', X, 8, Vector((0, 0.3, 0.3)))
for s in 'LR':
    P.rotate_world(rig, f'UpperArm_{s}', X, 35); P.rotate_world(rig, f'ForeArm_{s}', X, -55)
    P.rotate_world(rig, f'FrontPaw_{s}', X, 25)
    P.rotate_world(rig, f'Thigh_{s}', X, -20); P.rotate_world(rig, f'Shin_{s}', X, 30); P.rotate_world(rig, f'Hock_{s}', X, -25)
P.rotate_world(rig, 'Neck', X, 10)
shoot('crouch')
P.reset(rig)
P.rotate_world(rig, 'Neck', X, -12); P.rotate_world(rig, 'Head', X, -10); P.rotate_world(rig, 'Jaw', X, 38)
shoot('snarl', {'quarter': ((1.2, -2.6, 1.3), (0, -0.95, 0.95)), 'side': ((2.4, -0.95, 1.0), (0, -0.95, 0.95))}, 0.9)
P.reset(rig)
P.rotate_world(rig, 'Body', X, -15, Vector((0, 0.35, 0.05)))
P.rotate_world(rig, 'Scapula_L', X, -15)
P.rotate_world(rig, 'UpperArm_L', X, -75); P.rotate_world(rig, 'ForeArm_L', X, -40); P.rotate_world(rig, 'FrontPaw_L', X, -30)
shoot('swipe')
P.reset(rig)
P.rotate_world(rig, 'Body', Y, -85, Vector((-0.35, 0, 0.0)))
shoot('roll')
P.reset(rig)
P.rotate_world(rig, 'Neck', Z, 20); P.rotate_world(rig, 'Head', Z, 15)
for i in range(1, 9):
    P.rotate_world(rig, f'Tail{i}', Z, 10)
shoot('turn')
import json
json.dump(shots, open(os.path.join(HERE, 'work', '_stress.json'), 'w'))
print('STRESS', len(shots))
