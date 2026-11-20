"""Rest-pose spikes and pits on the skin (part 0) from the wrap (a notch on the mantle's back, slivers at the shoulders): a vertex
farther from its neighbours' mean than K x their mean edge length along its normal is moved onto the mean (a few rounds, then a
light relax of its ring). Topology and UVs stay (the paint belongs to work/uv_v1.blend). Region: the mantle's back (y > 0.15, z 0.45-0.82). Args: <in blend> <out blend> [K] [report only 0/1]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; K = float(a[2]) if len(a) > 2 else 0.6; RO = len(a) > 3 and a[3] == '1'
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['part']; bm.verts.ensure_lookup_table()
tot = set()
for r in range(4):
    bm.normal_update(); bad = []
    for v in bm.verts:
        if v[pl] != 0 or not v.link_edges or v.is_boundary: continue
        nb = [e.other_vert(v) for e in v.link_edges]
        if any(x[pl] != 0 for x in nb): continue
        if not (v.co.y > 0.15 and 0.45 < v.co.z < 0.82): continue      # the mantle's back only: the knee cops' points, sleeve rims and the belt boss are features
        c = sum((x.co for x in nb), Vector()) / len(nb); L = sum(e.calc_length() for e in v.link_edges) / len(nb)
        d = v.co - c
        if abs(d.dot(v.normal)) > K * L: bad.append((v, c))
    if RO and r == 0:
        for v, c in bad: print('SPIKE', tuple(round(x, 3) for x in v.co), round((v.co - c).length * 100, 2), 'cm')
        break
    for v, c in bad: v.co = c; tot.add(v.index)
    print('ROUND', r, len(bad))
    if not bad: break
if not RO:
    ring = {e.other_vert(bm.verts[i]) for i in tot for e in bm.verts[i].link_edges} | {bm.verts[i] for i in tot}
    for _ in range(2):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)) for v in ring if v[pl] == 0]
        for v, c in nw: v.co = v.co * 0.5 + c * 0.5
    bm.to_mesh(me); bm.free()
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print('SPIKES fixed', len(tot))
