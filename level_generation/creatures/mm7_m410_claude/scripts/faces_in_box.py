"""Probe: Body faces whose centre lies in a rest-pose box, with area, longest edge, the angle to their neighbours and
the class of the texel at their UV centre (work/material_classes.npy). Args: -- <blend> x0,x1 y0,y1 z0,z1"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
bx = [tuple(float(v) for v in s.split(',')) for s in a[1:4]]
me = bpy.data.objects['Body'].data; uv = me.uv_layers['UVMap'].data
cl = np.load(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'material_classes.npy'))
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices]); vf = {}
for p in me.polygons:
    for v in p.vertices:
        vf.setdefault(v, []).append(p.index)
for p in me.polygons:
    c = np.array(p.center)
    if not all(lo <= c[i] <= hi for i, (lo, hi) in enumerate(bx)):
        continue
    P = co[list(p.vertices)]; L = max(np.linalg.norm(P[(k + 1) % len(P)] - P[k]) for k in range(len(P)))
    nb = {f for v in p.vertices for f in vf[v]} - {p.index}
    dev = max((np.degrees(np.arccos(np.clip(np.dot(p.normal, me.polygons[f].normal), -1, 1))) for f in nb), default=0)
    u = np.mean([uv[l].uv for l in p.loop_indices], 0); cls = cl[int((1 - u[1]) * 1023), int(u[0] * 1023)]
    if dev > 60 or cls == 1:
        print(f'BOXFACE {p.index} piece {pv[p.vertices[0]]} class {cls} area {p.area * 1e4:.1f} cm2 long {L * 100:.1f} cm dev {dev:.0f} centre {np.round(c, 3)} verts {list(p.vertices)}')
