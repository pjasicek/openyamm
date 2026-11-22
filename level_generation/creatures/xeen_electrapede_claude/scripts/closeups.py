"""Clay close-ups of work/<blend> around given centres. Usage: closeups.py <blend> <prefix> y1 [y2 ...] (centre y)"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
for y in a[2:]:
    y = float(y)
    for name, d in {'l': (-2, 0, 0.3), 'r': (2, 0, 0.3), 'top': (0, 0.001, 3), 'under': (0, 0.001, -3),
                    'q': (-1.2, -1.2, 1.0)}.items():
        C.render((d[0], y + d[1], d[2]), (0, y, 0.1), 0.7, os.path.join(HERE, 'review', f'{a[1]}_{y:+.2f}_{name}.png'),
                 res=(500, 500), floor=False)
print('CLOSEUPS')
