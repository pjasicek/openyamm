"""Horizontal rays from x=0 outward (+x and -x) per station y and height z on the main shell only: where they escape
(the side mouth opening). Also the outer half-width (last hit) and the tooth row (teeth centroid x, z per y).
Args: -- <blend> <out json>"""
import bpy, sys, os, bmesh, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
comp = M.parts(bm); R = M.roles(bm, comp)
verts = [tuple(v.co) for v in bm.verts]
bvh = BVHTree.FromPolygons(verts, [[v.index for v in f.verts] for f in bm.faces if comp[f.verts[0].index] == R['shell']], all_triangles=True)
res = {'stations': [], 'teeth': []}
for y in np.round(np.arange(-5.2, -3.3, 0.05), 3):
    row = {'y': float(y), 'open': {}, 'hw': {}}
    for sgn in (1, -1):
        op = []; hw = []
        for z in np.round(np.arange(14.6, 15.6, 0.01), 3):
            o = Vector((0, y, z)); d = Vector((sgn, 0, 0)); last = None
            while True:
                h = bvh.ray_cast(o, d, 3)
                if h[0] is None: break
                last = h[0]; o = h[0] + d * 1e-4
            if last is None: op.append(float(z))
            else: hw.append((float(z), round(abs(last.x), 3)))
        row['open'][sgn] = op; row['hw'][sgn] = hw
    res['stations'].append(row)
CO = np.array(verts)
for k in R['teeth']:
    Pk = CO[comp == k]
    res['teeth'].append({'part': int(k), 'c': Pk.mean(0).round(3).tolist(), 'lo': Pk.min(0).round(3).tolist(), 'hi': Pk.max(0).round(3).tolist()})
json.dump(res, open(a[1], 'w'))
for r in res['stations']:
    o = r['open'][1]
    print(f"y {r['y']:.2f} open+x {(min(o), max(o), len(o)) if o else '-'}  open-x {(min(r['open'][-1]), max(r['open'][-1]), len(r['open'][-1])) if r['open'][-1] else '-'}")
for t in sorted(res['teeth'], key=lambda t: t['c'][1]):
    print('tooth', t)
