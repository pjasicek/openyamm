"""Numeric slices of the clean mesh pieces for joint placement: per piece, per 5 cm of y, the x/z extents and centre;
writes work/pieces.npz (vertex coords + piece label). Usage: slices.py <piece> [<piece>...]"""
import bpy, os, sys, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
want = [int(a) for a in sys.argv[sys.argv.index('--') + 1:]]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
m = bpy.data.objects['Dillo']
bm = bmesh.new(); bm.from_mesh(m.data); bm.verts.ensure_lookup_table()
seen = {}; pieces = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; seen[v.index] = 1; idx = []
    while stack:
        x = stack.pop(); idx.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen[o.index] = 1; stack.append(o)
    pieces.append(idx)
pieces.sort(key=len, reverse=True)
co = np.array([v.co[:] for v in bm.verts])
label = np.zeros(len(co), int)
for i, idx in enumerate(pieces): label[idx] = i
np.savez(os.path.join(HERE, 'work', 'pieces.npz'), co=co, label=label)
for i in want:
    c = co[label == i]
    print(f'SLICES piece {i}')
    for y0 in np.arange(c[:, 1].min(), c[:, 1].max(), 0.05):
        s = c[(c[:, 1] >= y0) & (c[:, 1] < y0 + 0.05)]
        if len(s) < 3: continue
        zs = np.sort(s[:, 2])
        # gaps in z (layers)
        gaps = [(round(zs[k], 2), round(zs[k + 1], 2)) for k in range(len(zs) - 1) if zs[k + 1] - zs[k] > 0.04]
        print(f'SL y {y0:+.2f} n {len(s):4d} x {s[:,0].min():+.2f}..{s[:,0].max():+.2f} z {zs[0]:.2f}..{zs[-1]:.2f} '
              f'c ({s[:,0].mean():+.2f},{s[:,2].mean():.2f}) zgaps {gaps}')
