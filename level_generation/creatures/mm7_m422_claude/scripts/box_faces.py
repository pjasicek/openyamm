"""Rest faces of a garment inside a box: centroid, longest edge, quality (shortest/longest), normal, piece; and a
render marking them. Args: -- <blend> <garment> x0 x1 y0 y1 z0 z1 [absx]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); g = int(a[1]); b = [float(x) for x in a[2:8]]; AX = len(a) > 8
me = bpy.data.objects['Body'].data
gv = np.array([x.value for x in me.attributes['garment'].data]); co = np.array([v.co[:] for v in me.vertices])
for p in me.polygons:
    if gv[p.vertices[0]] != g: continue
    c = np.array(p.center); x = abs(c[0]) if AX else c[0]
    if not (b[0] <= x <= b[1] and b[2] <= c[1] <= b[3] and b[4] <= c[2] <= b[5]): continue
    v = co[list(p.vertices)]; L = [np.linalg.norm(v[i] - v[(i + 1) % len(v)]) for i in range(len(v))]
    print('BOX', p.index, np.round(c, 3).tolist(), 'Lmax', round(max(L), 3), 'q', round(min(L) / max(L), 2), 'n', np.round(np.array(p.normal), 2).tolist())
