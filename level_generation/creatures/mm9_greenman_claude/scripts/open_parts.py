"""Open (non-closed) loose parts of 'Body' in a blend: count, triangles, by head/body set and by height. Args: <blend>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
hl = bm.faces.layers.int['head']; hn = bm.faces.layers.int['hand']
seen = set(); stats = {}
for f0 in bm.faces:
    if f0 in seen: continue
    st = [f0]; seen.add(f0); comp = []
    while st:
        f = st.pop(); comp.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen: seen.add(g); st.append(g)
    open_ = any(e.is_boundary for f in comp for e in f.edges)
    tris = sum(len(f.verts) - 2 for f in comp)
    key = ('open' if open_ else 'closed', 'head' if comp[0][hl] else 'hand' if comp[0][hn] else 'body', 'big' if tris > 500 else 'small')
    s = stats.setdefault(key, [0, 0]); s[0] += 1; s[1] += tris
for k, v in sorted(stats.items()):
    print('OPEN', k, 'parts', v[0], 'tris', v[1])
