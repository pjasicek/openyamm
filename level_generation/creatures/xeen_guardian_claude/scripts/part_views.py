"""Clay views of work/<blend> coloured by the face attribute 'part' (temporary materials, nothing saved).
Usage: part_views.py <blend> <prefix>  -> review/<prefix>_{front,quarter,side,gem,under}.png"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
mesh = bpy.data.objects['Skull']; me = mesh.data
COL = {0: (0.75, 0.74, 0.7), 1: (0.75, 0.6, 0.65), 2: (0.95, 0.95, 0.85), 3: (0.85, 0.95, 0.85),
       4: (0.55, 0.55, 0.6), 5: (0.9, 0.1, 0.1), 6: (0.1, 0.9, 0.2), 7: (0.1, 0.6, 0.9)}
parts = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', parts)
me.materials.clear()
for k in range(8):
    m = bpy.data.materials.new(f'p{k}'); m.diffuse_color = (*COL[k], 1); me.materials.append(m)
me.polygons.foreach_set('material_index', parts)
C.COLOR_OVERRIDE = 'MATERIAL'
V = {'front': ((0, -3, 0.42), (0, 0, 0.42), 0.95), 'quarter': ((-1.8, -2.2, 1.0), (0, 0, 0.42), 0.95),
     'side': ((3, 0, 0.42), (0, 0, 0.42), 0.95), 'gem': ((0.25, -1.5, 0.95), (0, -0.33, 0.52), 0.32),
     'under': ((0.4, -1.4, -0.6), (0, -0.2, 0.25), 0.7)}
for name, (loc, tgt, s) in V.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'{a[1]}_{name}.png'), res=(600, 600), floor=False)
print('VIEWS', a[1])
