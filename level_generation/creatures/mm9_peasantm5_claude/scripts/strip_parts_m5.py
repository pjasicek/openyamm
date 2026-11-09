"""PeasantM5 on Markel's master: delete Markel's small ornament parts (positions/UVs/weights of everything else unchanged):
every loose part under 100 vertices except the eyes (Head-weighted, above z 0.75) and the belt buckle (the largest small
part at the belt front). Gone: the torc/tie and pendant at the throat, the chest medallion, the placket lacing plates and
the belt studs (PeasantM5 wears a plain closed shirt and a plain belt).
Args: -- <in blend> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
CO = np.array([v.co[:] for v in bm.verts])
parts = []
for k in range(cid):
    m = comp == k
    parts.append((k, int(m.sum()), CO[m].mean(0), CO[m].min(0), CO[m].max(0)))
small = [p for p in parts if p[1] < 100]
eyes = [p for p in small if p[2][2] > 0.75]
belt = [p for p in small if 0.08 < p[2][2] < 0.22 and p[2][1] < -0.15]
buckle = max(belt, key=lambda p: p[1]) if belt else None
drop = [p for p in small if p not in eyes and p is not buckle]
dk = {p[0] for p in drop}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if comp[v.index] in dk], context='VERTS')
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
r = dict(parts=cid, kept_eyes=[(p[0], p[1]) for p in eyes], kept_buckle=(buckle[0], buckle[1]) if buckle else None,
         dropped=[(p[0], p[1], [round(x, 3) for x in p[2]]) for p in drop], dropped_vertices=int(sum(p[1] for p in drop)))
json.dump(r, open(a[2], 'w'), indent=1); print('STRIP', r['kept_eyes'], r['kept_buckle'], len(drop), r['dropped_vertices'])
