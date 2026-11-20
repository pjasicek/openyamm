"""Bat stress poses: rest (bones), wings up, wings down, folded, death sprawl. Args: out_prefix."""
import bpy, sys, os, math, subprocess
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bat as C
out = sys.argv[sys.argv.index('--') + 1]
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
            for k in (1, 2, 3):
                rot(f'Finger{k}a_{s}', Z, -sg * fold * 0.8)
POSES = {'rest': lambda: None, 'up': lambda: wings(55), 'down': lambda: wings(-45), 'fold': lambda: wings(10, 70),
         'sprawl': lambda: (rot('Spine1', X, 70), wings(-15), rot('Neck1', X, -20))}
cells = []
for name, fn in POSES.items():
    reset(); fn()
    for view, loc in (('front', (0.0, -1.6, 0.2)), ('q', (-1.0, -1.1, 0.6))):
        p = f'{out}_{name}_{view}.png'; C.render_ortho(loc, (0, 0, 0.15), 1.2, p, bones=(name == 'rest')); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', "import sys\nfrom PIL import Image\nims=[Image.open(p) for p in sys.argv[2:]]\nw,h=ims[0].size\no=Image.new('RGB',(w*2,h*(len(ims)//2)))\n[o.paste(im,((i%2)*w,(i//2)*h)) for i,im in enumerate(ims)]\no.save(sys.argv[1])", out + '_sheet.png'] + cells, check=True)
print('SHEET')
