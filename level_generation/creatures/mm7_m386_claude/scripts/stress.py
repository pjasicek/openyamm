"""Robot stress poses on work/rig_v1.blend -> review/stress_sheet.png: rest (bones), legs swung + spikes slid,
tail curled, neck/head turned, gun raised."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rig_v1.blend'))
import common_render as C
rig = bpy.data.objects['Robot_Rig']
def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()
def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()
def slide(name, dist):
    b = rig.pose.bones[name]; a = (b.tail - b.head).normalized()
    b.matrix = Matrix.Translation(a * dist) @ b.matrix; bpy.context.view_layer.update()
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def legs():
    rot('Leg_FL', X, 25); slide('Spike_FL', -0.08); rot('Leg_RR', X, -25); slide('Spike_RR', 0.06)
    rot('Leg_FR', Y, 20); rot('Leg_RL', Y, -20); slide('Spike_RL', -0.05)
def tail():
    for k in range(1, 9): rot(f'Tail{k}', X, -10)
def neck():
    rot('Neck1', Z, 25); rot('Head', X, 20); rot('Gun', X, -20)
POSES = {'rest': lambda: None, 'legs': legs, 'tail': tail, 'neck': neck}
cells = []
os.makedirs(os.path.join(HERE, 'review/stress'), exist_ok=True)
for name, fn in POSES.items():
    reset(); fn()
    for view, loc in (('side', (-1.6, 0, 0.3)), ('q', (-1.0, -1.1, 0.8))):
        p = os.path.join(HERE, f'review/stress/{name}_{view}.png')
        C.render_ortho(loc, (0, 0, 0.28), 1.1, p, bones=(name == 'rest'), mesh_name='Robot', rig_name='Robot_Rig'); cells.append(p)
C.sheet(os.path.join(HERE, 'review/stress_sheet.png'), cells, 4)
print('SHEET')
