"""Clay views of one object of a blend: front, side (creature's left = +X camera), back, quarter, top.
Args: -- <blend relative to the project> <object> <out prefix relative to the project> [ortho scale] [centre z]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, a[0]))
C.MESH = a[1]
s = float(a[3]) if len(a) > 3 else 2.1
cz = float(a[4]) if len(a) > 4 else 0.95
for name, (loc, tgt) in {'front': ((0, -5, cz), (0, 0, cz)), 'left': ((5, 0, cz), (0, 0, cz)),
                         'back': ((0, 5, cz), (0, 0, cz)), 'quarter': ((3.2, -3.8, cz + 1.2), (0, 0, cz)),
                         'right': ((-5, 0, cz), (0, 0, cz))}.items():
    C.render(loc, tgt, s, os.path.join(HERE, f'{a[2]}_{name}.png'), res=(500, 500), floor=False)
