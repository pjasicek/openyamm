"""Texture pass probe: pieces of Body in a blend, sizes, surface, overlapping (mirrored) UV pieces, FitPose. Args: <blend>"""
import bpy, sys, json, bmesh
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
print('objs', [o.name for o in bpy.data.objects], 'actions', [a.name for a in bpy.data.actions][:30])
print('attrs', [(a.name, a.domain, a.data_type) for a in me.attributes], 'uv', [u.name for u in me.uv_layers], 'mw', body.matrix_world == rig.matrix_world)
print('polys', len(me.polygons), 'verts', len(me.vertices), 'tri only', all(len(p.vertices) == 3 for p in me.polygons), 'mods', [m.type for m in body.modifiers])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
n = len(me.vertices); comp = np.full(n, -1); N = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = N
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = N; st.append(y)
    N += 1
tri = np.array([p.vertices[:] for p in me.polygons]); pos = np.array([v.co for v in me.vertices])
p3 = pos[tri]; a3 = np.linalg.norm(np.cross(p3[:, 1]-p3[:, 0], p3[:, 2]-p3[:, 0]), axis=1)/2
fc = comp[tri[:, 0]]
uv = np.zeros(len(me.loops)*2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
fuv = np.array([uv[list(p.loop_indices)] for p in me.polygons])
rows = []
for k in range(N):
    f = fc == k
    c = pos[tri[f]].reshape(-1, 3).mean(0)
    grp = {}
    for v in np.nonzero(comp == k)[0]:
        for g in me.vertices[v].groups:
            nm = body.vertex_groups[g.group].name; grp[nm] = grp.get(nm, 0) + g.weight
    d = max(grp, key=grp.get) if grp else '-'
    rows.append((k, int(f.sum()), float(a3[f].sum()), [round(float(x), 3) for x in c], d, [round(float(x), 3) for x in fuv[f].reshape(-1, 2).mean(0)]))
rows.sort(key=lambda r: -r[1])
tot = a3.sum()
print('pieces', N, 'surface', tot)
for r in rows:
    print(r[0], r[1], f'{100*r[2]/tot:.2f}%', r[3], r[4], r[5])
for t in (8, 12, 20, 40, 80):
    s = [r for r in rows if r[1] < t]
    print(f'pieces under {t} tris: {len(s)}, {100*sum(r[2] for r in s)/tot:.2f}% of surface')
