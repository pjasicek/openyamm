"""Dump the vertices and triangles of the Skull mesh in work/<blend> to work/<out>.npz. Usage: dump_mesh.py <blend> <out>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
me = bpy.data.objects['Skull'].data
me.calc_loop_triangles()
co = np.array([tuple(v.co) for v in me.vertices]); tri = np.array([tuple(t.vertices) for t in me.loop_triangles])
np.savez(os.path.join(HERE, 'work', a[1]), co=co, tri=tri)
print('DUMPED', len(co), len(tri))
