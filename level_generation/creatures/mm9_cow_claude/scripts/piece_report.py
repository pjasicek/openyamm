"""Report the separate pieces of 'Body' (centroid, size, dominant bone). Args: <rig blend>"""
import bpy, bmesh, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); out = []
for v in bm.verts:
    if v.index in seen:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    if len(comp) > 3000:
        continue
    c = sum((me.vertices[i].co for i in comp), me.vertices[comp[0]].co * 0) / len(comp)
    w = {}
    for i in comp:
        for g in me.vertices[i].groups:
            n = ob.vertex_groups[g.group].name
            w[n] = w.get(n, 0) + g.weight
    out.append({'n': len(comp), 'c': [round(x, 3) for x in c], 'bones': sorted(w.items(), key=lambda kv: -kv[1])[:2]})
print('PIECES ' + json.dumps(out))
