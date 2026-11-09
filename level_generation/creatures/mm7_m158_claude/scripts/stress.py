"""Bat stress poses on work/rig_v1.blend: rest (bones), wings up, wings down, folded, sprawl -> review/stress_sheet.png."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rig_v1.blend'))
import common_bat as C
rig = bpy.data.objects['Bat_Rig']
def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()
def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()
Y = (0, 1, 0); X = (1, 0, 0); Z = (0, 0, 1)
def wings(up, fold=0.0):
    for s, sg in (('L', 1), ('R', -1)):
        rot(f'UpperArm_{s}', Y, -sg * up)
        rot(f'ForeArm_{s}', Y, -sg * up * 0.4)
        if fold:
            rot(f'ForeArm_{s}', Z, -sg * fold)
            for k in (1, 2, 3, 4):
                rot(f'Finger{k}a_{s}', Z, -sg * fold * 0.8)
POSES = {'rest': lambda: None, 'up': lambda: wings(55), 'down': lambda: wings(-45), 'fold': lambda: wings(10, 70),
         'sprawl': lambda: (rot('Spine1', X, 50), wings(-15), rot('Neck1', X, -20), rot('Ear_L', Y, -30))}
cells = []
os.makedirs(os.path.join(HERE, 'review/stress'), exist_ok=True)
for name, fn in POSES.items():
    reset(); fn()
    for view, loc in (('front', (0.0, -1.6, 0.12)), ('q', (-1.0, -1.1, 0.7))):
        p = os.path.join(HERE, f'review/stress/{name}_{view}.png')
        C.render_ortho(loc, (0, 0, 0.1), 1.1, p, bones=(name == 'rest')); cells.append(p)
C.sheet(os.path.join(HERE, 'review/stress_sheet.png'), cells, 2)
print('SHEET')
