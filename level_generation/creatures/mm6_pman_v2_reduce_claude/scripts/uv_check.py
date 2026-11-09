"""Master sanity before paying: every vertex weighted, UV coverage and overlap per layer (1024 raster)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
b = bpy.data.objects['Body']; me = b.data
print('UNWEIGHTED', sum(1 for v in me.vertices if not v.groups), 'groups', len(b.vertex_groups), 'mods', [m.type for m in b.modifiers])
head = np.array([a.value for a in me.attributes['head'].data])
me.calc_loop_triangles(); N = 1024
for layer, want in [('UVMap', None), ('HeadUV', 1)]:
    hits = np.zeros((N, N), np.uint16); uv = me.uv_layers[layer].data; deg = 0
    for t in me.loop_triangles:
        if want is not None and head[t.polygon_index] != want: continue
        a, bb, c = [np.array(uv[l].uv) * N for l in t.loops]
        den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
        if abs(den) < 1e-9: deg += 1; continue
        x0, y0 = np.maximum(np.floor(np.minimum(np.minimum(a, bb), c)).astype(int), 0); x1, y1 = np.minimum(np.ceil(np.maximum(np.maximum(a, bb), c)).astype(int), N - 1)
        x, y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w0 = ((bb[1] - c[1]) * (x - c[0]) + (c[0] - bb[0]) * (y - c[1])) / den; w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
        m = (w0 > 1e-6) & (w1 > 1e-6) & (1 - w0 - w1 > 1e-6); hits[(y[m] - .5).astype(int), (x[m] - .5).astype(int)] += 1
    print('UV', layer, 'coverage', round(float((hits > 0).mean()), 3), 'overlap px', int((hits > 1).sum()), 'degenerate', deg)
