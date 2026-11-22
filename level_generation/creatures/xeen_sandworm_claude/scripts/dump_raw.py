"""Dump vertices and triangles of work/<blend> object Worm to work/<name>.npz. Usage: dump_raw.py <blend> <name>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
me = bpy.data.objects['Worm'].data
me.calc_loop_triangles()
co = np.array([v.co[:] for v in me.vertices])
tris = np.array([t.vertices[:] for t in me.loop_triangles])
extra = {}
if 'part' in me.attributes:
    extra['fpart'] = np.array([me.attributes['part'].data[t.polygon_index].value for t in me.loop_triangles])
np.savez(os.path.join(HERE, 'work', a[1] + '.npz'), co=co, tris=tris, **extra)
print('DUMPED', len(co), len(tris))
