"""MM9 faces whose skin texel (UV centroid) is mouth-red: count per bone, bounds. Args: src blend skin png"""
import bpy, sys
import numpy as np

from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
img = bpy.data.images.load(argv[1]); W0, H0 = img.size; sk = np.array(img.pixels[:], np.float32).reshape(H0, W0, 4)[::-1, :, :3]
H, W = sk.shape[:2]
c = Counter(); pts = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.endswith('.mesh'):
        continue
    me = o.data; uv = me.uv_layers.active.data
    vl = [o.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name for v in me.vertices]
    for p in me.polygons:
        u = np.mean([tuple(uv[l].uv) for l in p.loop_indices], 0)
        px = sk[int(np.clip((1 - u[1]) * H, 0, H - 1)), int(np.clip(u[0] * W, 0, W - 1))]
        r, g, b = px
        if r > 0.35 and r > 1.6 * g and r > 1.6 * b:
            c[vl[p.vertices[0]]] += 1
            pts += [tuple(o.matrix_world @ me.vertices[i].co) for i in p.vertices]
P = np.array(pts)
print('MOUTH', dict(c), P.min(0).round(2) if len(P) else None, P.max(0).round(2) if len(P) else None)
