"""Clay views of work/<blend> (object Worm) for reading the mesh: side, top, under, front, quarter, plus a head
close-up. Usage: views.py <blend> <prefix> [bones]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
bones = len(a) > 2 and a[2] == 'bones'
V = {'side': ((-4, 0, 0.2), (0, 0, 0.2), 2.5, (1600, 560)), 'top': ((0, 0, 4), (0, 0, 0), 2.5, (1600, 700)),
     'under': ((0, 0, -4), (0, 0, 0), 2.5, (1600, 700)), 'front': ((0, -4, 0.2), (0, 0, 0.2), 0.8, (800, 500)),
     'quarter': ((-2.2, -2.4, 1.4), (0, -0.2, 0.1), 2.6, (1600, 900)),
     'head': ((-1.2, -2.2, 0.6), (0, -0.95, 0.18), 0.7, (900, 700))}
for name, (loc, tgt, s, res) in V.items():
    if name == 'top' or name == 'under':
        cam = (loc, tgt)
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'{a[1]}_{name}.png'), res=res, floor=False, bones=bones)
print('VIEWS', a[1])
