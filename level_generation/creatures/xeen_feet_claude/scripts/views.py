"""Clay views of one object in a blend: views.py <blend in work/> <object> <prefix> [ortho scale] [textured 0/1]
-> review/<prefix>_{front,side,top,quarter,under}.png and review/<prefix>_sheet.png"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
obj = bpy.data.objects[a[1]]; prefix = a[2]
s = float(a[3]) if len(a) > 3 else 0.36
tex = len(a) > 4 and a[4] == '1'
import numpy as np
dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh()
co = np.array([obj.matrix_world @ v.co for v in me.vertices]); ev.to_mesh_clear()
c = (co.min(0) + co.max(0)) / 2
V = {'front': (0, -3, 0), 'side': (3, 0, 0), 'top': (0, 0.001, 3), 'quarter': (2, -2.4, 1.4), 'under': (0, 0.001, -3),
     'oside': (-3, 0, 0)}
paths = []
for k, off in V.items():
    p = os.path.join(HERE, 'review', f'{prefix}_{k}.png')
    C.render(tuple(c + off), tuple(c), s, p, res=(520, 420), floor=False, textured=tex, extra=(a[1],))
    paths.append(p)
print('VIEWS', prefix)
