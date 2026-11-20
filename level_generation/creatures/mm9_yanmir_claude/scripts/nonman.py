"""Where the non-manifold and boundary edges of Body are. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body'].data)
nm = [e for e in bm.edges if not e.is_manifold]
P = np.array([(e.verts[0].co + e.verts[1].co)[:] for e in nm]) / 2
print('NONMAN', len(nm), 'wire', sum(1 for e in nm if not e.link_faces), 'boundary', sum(1 for e in nm if len(e.link_faces) == 1), 'multi', sum(1 for e in nm if len(e.link_faces) > 2))
if len(P):
    H, edges = np.histogramdd(P, bins=(4, 4, 12)); idx = np.argwhere(H > 0)
    for i in idx[np.argsort(-H[tuple(idx.T)])][:12]:
        print('CELL', [round(float(edges[a][i[a]]), 2) for a in range(3)], int(H[tuple(i)]))
part = bm.verts.layers.int.get('part')
print('PARTS', np.bincount([v[part] for v in bm.verts]) if part else None)
