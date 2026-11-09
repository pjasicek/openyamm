"""Weights of the vertices inside a rest-space box. Args: -- <blend> x0 x1 y0 y1 z0 z1"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); b = [float(x) for x in a[1:7]]
body = bpy.data.objects['Body']; me = body.data
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]
for v in me.vertices:
    x, y, z = v.co
    if b[0] <= x <= b[1] and b[2] <= y <= b[3] and b[4] <= z <= b[5]:
        print('W', v.index, 'g', gv[v.index], 'p', pv[v.index], tuple(round(c, 3) for c in v.co), ' '.join(f'{names[e.group]}:{e.weight:.2f}' for e in sorted(v.groups, key=lambda e: -e.weight)[:5]))
