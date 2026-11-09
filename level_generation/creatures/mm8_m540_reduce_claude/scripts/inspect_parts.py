"""Rest-pose source parts: connected components, UV ranges, dominant bones (orientation only, prints)."""
import os, bpy, bmesh, numpy as np, collections
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data
print('GROUPS', [g.name for g in src.vertex_groups])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
comp = [-1] * len(bm.faces); c = 0
for f in bm.faces:
    if comp[f.index] >= 0: continue
    st = [f]; comp[f.index] = c
    while st:
        g = st.pop()
        for e in g.edges:
            for h in e.link_faces:
                if comp[h.index] < 0: comp[h.index] = c; st.append(h)
    c += 1
names = {g.index: g.name for g in src.vertex_groups}
rows = []
for k in range(c):
    fs = [f for f in bm.faces if comp[f.index] == k]
    us = np.array([l[uvl].uv[0] for f in fs for l in f.loops]); vs = np.array([l[uvl].uv[1] for f in fs for l in f.loops])
    co = np.array([v.co[:] for f in fs for v in f.verts])
    w = collections.Counter()
    for f in fs:
        for v in f.verts:
            for g in me.vertices[v.index].groups: w[names[g.group]] += g.weight
    tris = sum(len(f.verts) - 2 for f in fs)
    rows.append((tris, k, us.min(), us.max(), co.min(0), co.max(0), w.most_common(3)))
for r in sorted(rows, key=lambda r: -r[0]):
    print('COMP', r[1], r[0], 'u %.3f-%.3f' % (r[2], r[3]), 'z %.3f-%.3f' % (r[4][2], r[5][2]), [(n, round(x, 1)) for n, x in r[6]])
