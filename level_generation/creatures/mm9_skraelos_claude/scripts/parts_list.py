"""List loose parts of 'Body' (numbered by lowest vertex index, as head_split.py): vertices, head-face share, bbox. Args: <blend>"""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data; bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']
comp = -np.ones(len(bm.verts), np.int64); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
co = np.array([v.co[:] for v in bm.verts])
for k in range(cid):
    m = comp == k
    fs = [f for f in bm.faces if comp[f.verts[0].index] == k]
    print('PART', k, int(m.sum()), 'head %.2f' % (np.mean([f[hl] for f in fs]) if fs else 0), co[m].min(0).round(3).tolist(), co[m].max(0).round(3).tolist())
