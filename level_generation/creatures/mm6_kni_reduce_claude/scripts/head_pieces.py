"""Connected pieces of work/sym.blend's Body above the collar (centre z > 1.42 m): faces, centre, size, dominant
bone. Usage: blender -b work/sym.blend -P head_pieces.py"""
import bpy, bmesh
import numpy as np
o = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active; names = {g.index: g.name for g in o.vertex_groups}
seen = set()
for f in bm.faces:
    if f.index in seen:
        continue
    stack, piece = [f], []; seen.add(f.index)
    while stack:
        g = stack.pop(); piece.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index); stack.append(h)
    vs = list({v for g in piece for v in g.verts}); co = np.array([v.co[:] for v in vs])
    if co[:, 2].mean() < 1.42:
        continue
    w = {}
    for v in vs:
        for k, x in v[dl].items():
            w[names[k]] = w.get(names[k], 0) + x
    print('PIECE', piece[0].index, len(piece), 'centre', co.mean(0).round(3), 'size', np.ptp(co, 0).round(3), max(w, key=w.get))
