"""Extreme poses on work/<blend> (default rig_v1.blend) before animating: rest; rear (front up, both forelegs raised
forward with the claws out, as native att 1-2); mace (tail arched over the back, the ball above the head, spikes out,
as native att 2); roll onto the right side; curl (head tucked, shoulders hunched, tail curled round, as native att 3);
tongue out with the head turned. Writes review/stress_<pose>_<cam>.png and review/stress_sheet.png."""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a else 'rig_v1.blend'))
rig = bpy.data.objects['Dillo_Rig']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
CAMS = {'quarter': ((2.4, -2.8, 1.6), (0, 0.0, 0.3)), 'side': ((4, 0, 0.45), (0, 0, 0.45))}
shots = []


def shoot(name):
    for c, (loc, tgt) in CAMS.items():
        p = os.path.join(HERE, 'review', f'stress_{name}_{c}.png'); shots.append(p)
        C.render(loc, tgt, 2.7, p, res=(600, 480))


def scale(name, s):
    b = rig.pose.bones[name]; b.scale = (s, s, s); bpy.context.view_layer.update()


P.reset(rig); scale('Spikes', 0.4); scale('Tongue', 0.05); shoot('rest')
P.reset(rig)
P.rotate_world(rig, 'Body', X, -14, Vector((0, 0.1, 0.05)))
for s, sg in (('L', 1), ('R', -1)):
    P.rotate_world(rig, f'UpperArm_{s}', X, -55); P.rotate_world(rig, f'ForeArm_{s}', X, -30)
    P.rotate_world(rig, f'UpperArm_{s}', Y, -sg * 20)
scale('Spikes', 0.4); scale('Tongue', 0.05)
shoot('rear')
P.reset(rig)
for i in range(1, 9):
    P.rotate_world(rig, f'Tail{i}', X, 26 if i > 1 else 15)
scale('Spikes', 1.0); scale('TailBall', 1.3); scale('Tongue', 0.05)
shoot('mace')
P.reset(rig)
P.rotate_world(rig, 'Body', Y, 85, Vector((-0.38, 0, 0.0)))
scale('Spikes', 0.4); scale('Tongue', 0.05)
shoot('roll')
P.reset(rig)
P.rotate_world(rig, 'Neck', X, 25); P.rotate_world(rig, 'Head', X, 25)
P.rotate_world(rig, 'Chest', X, 10)
for i in range(1, 9):
    P.rotate_world(rig, f'Tail{i}', Z, 20)
scale('Spikes', 0.4); scale('Tongue', 0.05)
shoot('curl')
P.reset(rig)
P.rotate_world(rig, 'Head', Z, 25); P.rotate_world(rig, 'Neck', Z, 10)
scale('Spikes', 0.4); scale('Tongue', 1.0)
shoot('tongue')
