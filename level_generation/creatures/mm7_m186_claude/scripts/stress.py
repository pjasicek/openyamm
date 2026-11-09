"""Dragonfly stress poses on work/rig_v1.blend -> review/stress_sheet.png: rest (bones), abdomen curled forward,
abdomen straightened back, wings up / down with head turn, claw swing."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rig_v1.blend'))
import common_render as C
rig = bpy.data.objects['Dragonfly_Rig']
def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()
def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def abd(deg):
    for k in range(1, 11): rot(f'Abd{k}', X, deg)
def wings(f, h):
    for s, sg in (('L', 1), ('R', -1)):
        rot(f'ForeWing_{s}', Y, -sg * f); rot(f'HindWing_{s}', Y, -sg * h)
POSES = {'rest': lambda: None, 'curl': lambda: abd(-12), 'straight': lambda: abd(10),
         'wings': lambda: (wings(40, -30), rot('Head', Z, 25)), 'claw': lambda: (rot('Claw', X, -60), abd(-6), wings(-35, 35))}
cells = []
os.makedirs(os.path.join(HERE, 'review/stress'), exist_ok=True)
for name, fn in POSES.items():
    reset(); fn()
    for view, loc in (('side', (-1.6, 0, 0.26)), ('q', (-1.0, -1.1, 0.75))):
        p = os.path.join(HERE, f'review/stress/{name}_{view}.png')
        C.render_ortho(loc, (0, 0, 0.24), 1.05, p, bones=(name == 'rest'), mesh_name='Dragonfly', rig_name='Dragonfly_Rig'); cells.append(p)
C.sheet(os.path.join(HERE, 'review/stress_sheet.png'), cells, 4)
print('SHEET')
