"""Dump vertex positions, per-vertex part and triangles of work/<blend> (object Mole) to work/<name>.npz.
Usage: dump_mesh.py <blend> <name>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
me = bpy.data.objects['Saber'].data
co = np.array([v.co[:] for v in me.vertices])
part = np.zeros(len(co), int)
tris = []
for p in me.polygons:
    pv = me.attributes['part'].data[p.index].value
    for v in p.vertices: part[v] = pv
    tris.append(list(p.vertices)[:3])
np.savez(os.path.join(HERE, 'work', a[1] + '.npz'), co=co, part=part, tris=np.array(tris))
print('DUMPED', len(co))
