"""Rasterise the faces that touch a vertex moved by despike.py (work/despike_moved.json) in both texture layouts at
N x N, with their rest-pose positions: work/moved_raster.npz (layer, row, col, pos). Args: -- <blend> <N>"""
import bpy, sys, os, json
import numpy as np
blend, N = sys.argv[sys.argv.index('--') + 1:]; N = int(N)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Body'].data; co = np.array([tuple(v.co) for v in me.vertices])
moved = set(json.load(open(os.path.join(HERE, 'work', 'despike_moved.json')))['moved'])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.calc_loop_triangles(); out = {'layer': [], 'row': [], 'col': [], 'pos': []}
for t in me.loop_triangles:
    if not set(t.vertices) & moved:
        continue
    layer = 'HeadUV' if hd[t.polygon_index] else 'UVMap'; uv = me.uv_layers[layer].data
    P = np.array([tuple(uv[l].uv) for l in t.loops]) * N; X = co[list(t.vertices)]
    x0, y0 = np.maximum(np.floor(P.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(P.max(0)).astype(int) + 1, N - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = P; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den; w2 = 1 - w0 - w1
    m = (w0 >= -0.15) & (w1 >= -0.15) & (w2 >= -0.15)                   # one texel of margin for the seams
    W = np.stack([w0[m], w1[m], w2[m]], 1).clip(0); W /= W.sum(1, keepdims=True)
    out['layer'] += [layer == 'HeadUV'] * int(m.sum()); out['row'] += list((N - 1 - (ys[m] - 0.5)).astype(int))
    out['col'] += list((xs[m] - 0.5).astype(int)); out['pos'] += list(W @ X)
np.savez(os.path.join(HERE, 'work', 'moved_raster.npz'), **{k: np.array(v) for k, v in out.items()})
print('MOVEDRASTER faces of', len(moved), 'moved vertices:', len(out['row']), 'texels')
