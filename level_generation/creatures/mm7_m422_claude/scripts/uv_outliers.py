"""Faces whose UV triangle is far larger than its 3D size implies (seam-crossing faces after a UV carry-over or
transfer): per layer the ratio sqrt(uv area) / sqrt(3D area) against the layer median. Args: -- <blend> [factor]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); F = float(a[1]) if len(a) > 1 else 4.0
me = bpy.data.objects['Body'].data; me.calc_loop_triangles()
hd = np.array([x.value for x in me.attributes['head'].data]) if 'head' in me.attributes else np.zeros(len(me.polygons))
pv = np.array([x.value for x in me.attributes['piece'].data])
co = np.array([v.co[:] for v in me.vertices])
for layer in [l.name for l in me.uv_layers]:
    uv = me.uv_layers[layer].data
    rs, ids = [], []
    for t in me.loop_triangles:
        if (layer == 'HeadUV') != bool(hd[t.polygon_index]):
            continue
        P = co[list(t.vertices)]; U = np.array([uv[l].uv[:] for l in t.loops])
        a3 = np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0])) / 2; a2 = abs(np.cross(U[1] - U[0], U[2] - U[0])) / 2
        if a3 > 1e-9:
            rs.append(np.sqrt(a2 / a3)); ids.append(t.polygon_index)
    rs = np.array(rs); med = np.median(rs); bad = rs > F * med
    pcs = {}
    for k in np.where(bad)[0]:
        p = int(pv[me.polygons[ids[k]].vertices[0]]); pcs[p] = pcs.get(p, 0) + 1
    print('UVOUT', layer, 'triangles', len(rs), 'median', round(float(med), 3), f'> {F}x', int(bad.sum()), 'by piece', pcs)
