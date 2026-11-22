"""Extreme poses on work/rig_v1.blend before animating: rest, swipe (both arms raised forward and up, claws curled),
paddle (left hand reaching forward, right swept back), rear (front up, head up), roll onto the right side, head and
tail turn. Writes review/stress_<pose>_<cam>.png and review/stress_sheet.png."""
import bpy, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig = bpy.data.objects['Mole_Rig']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
CAMS = {'quarter': ((2.2, -2.8, 1.5), (0, -0.1, 0.3)), 'side': ((3.5, 0, 0.4), (0, 0, 0.35))}
shots = []


def shoot(name):
    for c, (loc, tgt) in CAMS.items():
        p = os.path.join(HERE, 'review', f'stress_{name}_{c}.png'); shots.append(p)
        C.render(loc, tgt, 2.0, p, res=(600, 480))


P.reset(rig); shoot('rest')
P.reset(rig)
P.rotate_world(rig, 'Body', X, 12, Vector((0, 0.3, 0.1)))
for s, sg in (('L', 1), ('R', -1)):
    P.rotate_world(rig, f'UpperArm_{s}', Y, -sg * 35); P.rotate_world(rig, f'UpperArm_{s}', X, 30)
    P.rotate_world(rig, f'ForeArm_{s}', X, 25)
    P.rotate_local(rig, f'Claws_{s}', 'X', 35)
shoot('swipe')
P.reset(rig)
P.rotate_world(rig, 'UpperArm_L', Z, -30); P.rotate_world(rig, 'UpperArm_R', Z, -35)
P.rotate_world(rig, 'Thigh_L', X, 25); P.rotate_world(rig, 'Thigh_R', X, -25)
shoot('paddle')
P.reset(rig)
P.rotate_world(rig, 'Body', X, 28, Vector((0, 0.45, 0.05)))
P.rotate_world(rig, 'Head', X, 18); P.rotate_world(rig, 'Snout', X, 15)
shoot('rear')
P.reset(rig)
P.rotate_world(rig, 'Body', Y, 85, Vector((-0.3, 0, 0.0)))
for s in 'LR':
    P.rotate_local(rig, f'Claws_{s}', 'X', 50)
shoot('roll')
P.reset(rig)
P.rotate_world(rig, 'Head', Z, 25); P.rotate_world(rig, 'Snout', Z, 12)
for i in range(1, 5):
    P.rotate_world(rig, f'Tail{i}', Z, 15)
shoot('turn')
