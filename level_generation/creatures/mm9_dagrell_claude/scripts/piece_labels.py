"""Per piece of the rigged 'Body' (rig blend): size, dominant bone(s), bind-space bbox. Args: <rig blend> [min verts]"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
mn = int(argv[1]) if len(argv) > 1 else 60
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = np.full(len(bm.verts), -1); comps = []
for v in bm.verts:
    if seen[v.index] >= 0: continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if seen[y.index] < 0: seen[y.index] = len(comps); st.append(y)
    comps.append(c)
names = {g.index: g.name for g in ob.vertex_groups}
for k, c in sorted(enumerate(comps), key=lambda kc: -len(kc[1])):
    if len(c) < mn: continue
    w = {}
    for i in c:
        for g in me.vertices[i].groups:
            w[names[g.group]] = w.get(names[g.group], 0) + g.weight
    top = sorted(w.items(), key=lambda kv: -kv[1])[:3]
    P = np.array([tuple(me.vertices[i].co) for i in c])
    print('PIECE', k, len(c), [(a, round(b / len(c), 2)) for a, b in top], [round(x, 2) for x in P.min(0)], [round(x, 2) for x in P.max(0)])
