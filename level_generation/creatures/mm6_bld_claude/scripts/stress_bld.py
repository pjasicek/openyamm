"""Bloodsucker stress poses: rest (bones), wings level, wings down, mouth open, tail curl, death coil.
Args: out_prefix."""
import bpy, sys, os, math, subprocess
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_bld as C
out = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Bld_Rig']


def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
        b.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def rot(name, axis, deg):
    b = rig.pose.bones[name]; h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h) \
        @ b.matrix
    bpy.context.view_layer.update()


Y = (0, 1, 0); X = (1, 0, 0); Z = (0, 0, 1)


def wings(down, elbow=0.0):
    for s, sg in (('L', 1), ('R', -1)):
        rot(f'UpperArm_{s}', Y, sg * down)
        if elbow:
            rot(f'ForeArm_{s}', Y, sg * elbow)


def mouth(k):
    rig.pose.bones['Mouth'].scale = (k, 1, k); bpy.context.view_layer.update()


def tail(deg):
    for i in range(1, 7):
        rot(f'Tail{i}', Z, deg)


POSES = {'rest': lambda: None, 'level': lambda: wings(60), 'down': lambda: wings(105, 20),
         'mouth': lambda: (mouth(2.4), rot('Neck1', X, -20)), 'tail': lambda: tail(18),
         'coil': lambda: (rot('Spine1', X, -60), tail(25), rot('Neck1', X, 30), wings(80))}
cells = []
for name, fn in POSES.items():
    reset(); fn()
    for view, loc in (('front', (0.0, -1.6, 0.25)), ('q', (-1.1, -1.0, 0.7))):
        p = f'{out}_{name}_{view}.png'; C.render_ortho(loc, (0, 0, 0.2), 1.3, p, bones=(name == 'rest')); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', "import sys\nfrom PIL import Image\nims=[Image.open(p) for p in sys.argv[2:]]\n"
                "w,h=ims[0].size\no=Image.new('RGB',(w*4,h*((len(ims)+3)//4)))\n"
                "[o.paste(im,((i%4)*w,(i//4)*h)) for i,im in enumerate(ims)]\no.save(sys.argv[1])",
                out + '_sheet.png'] + cells, check=True)
print('SHEET')
