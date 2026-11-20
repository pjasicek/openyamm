"""Longest edges of the Body (rest), optionally limited to faces with the 'head' attribute. Args: -- <blend> [head]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
co = np.array([v.co[:] for v in me.vertices]); pv = np.array([x.value for x in me.attributes['piece'].data])
fl = [p for p in me.polygons if (len(a) < 2 or me.attributes['head'].data[p.index].value)]
E = {tuple(sorted(e)) for p in fl for e in p.edge_keys}
E = np.array(list(E)); L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
for k in np.argsort(-L)[:12]:
    print('LONG', round(float(L[k]), 3), np.round(co[E[k, 0]], 3), np.round(co[E[k, 1]], 3), 'pieces', pv[E[k, 0]], pv[E[k, 1]])
