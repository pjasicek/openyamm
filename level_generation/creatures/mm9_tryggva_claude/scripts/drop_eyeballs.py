"""Delete Meshy's loose eyeball pieces (mm9_tryggva face fix): two ~35-vertex parts in front of the sockets (z 0.79-0.83,
y < -0.07, |x| < 0.06) that sat off-centre in the jagged sockets (one poked through the lids after eye_relax.py). The face
then carries painted eyes on the relaxed socket surface (as PeasantM1's projected Codex eye area). Other geometry,
UVs, weights and attributes unchanged. Args (Blender): -- <in blend> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
CO = np.array([v.co[:] for v in bm.verts])
drop = []
for k in range(cid):
    m = comp == k
    lo, hi = CO[m].min(0), CO[m].max(0)
    if m.sum() < 60 and lo[2] > 0.785 and hi[2] < 0.835 and hi[1] < -0.07 and np.abs(CO[m, 0]).max() < 0.06:
        drop.append((k, int(m.sum()), lo.round(3).tolist(), hi.round(3).tolist()))
ids = {d[0] for d in drop}
faces = [f for f in bm.faces if comp[f.verts[0].index] in ids]
bmesh.ops.delete(bm, geom=faces, context='FACES')
bm.to_mesh(body.data); bm.free(); body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('DROP_EYEBALLS', json.dumps({'parts': drop, 'faces': len(faces)}))
