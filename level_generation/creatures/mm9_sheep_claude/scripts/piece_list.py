"""List connected components of 'Body' (verts, bbox, dominant group). Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
seen = set()
for v in bm.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    if len(c) > 50000:
        print('PIECE main', len(c)); continue
    P = np.array([tuple(o.data.vertices[i].co) for i in c])
    g = {}
    for i in c:
        for gg in o.data.vertices[i].groups:
            n = o.vertex_groups[gg.group].name; g[n] = g.get(n, 0) + gg.weight
    print('PIECE', len(c), P.min(0).round(3).tolist(), P.max(0).round(3).tolist(), sorted(g.items(), key=lambda t: -t[1])[:3])
