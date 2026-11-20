import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[1])
mm = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
M = np.array([tuple(mm.matrix_world @ v.co) for v in mm.data.vertices])
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lk = bm.faces.layers.int['head']
comp = -np.ones(len(bm.verts), int); k = 0; sizes = []
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = k; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = k; st.append(o)
    sizes.append(n); k += 1
CO = np.array([tuple(ob.matrix_world @ v.co) for v in bm.verts])
headv = np.array([any(f[lk] for f in v.link_faces) for v in bm.verts])
C = np.array([-0.005, 0.04, 0.80])
for k2 in range(k):
    m = (comp == k2) & headv
    if m.sum() > 150 and CO[m, 2].mean() > 0.62:
        q = CO[m]; print('HP part', k2, int(m.sum()), np.round(q.min(0), 3), np.round(q.max(0), 3))
def prof(P, label):
    out = []
    for z in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
        s = P[np.abs(P[:, 2] - z) < 0.02]
        if len(s) == 0: out.append(None); continue
        out.append((round(float(s[:, 0].min()), 3), round(float(s[:, 0].max()), 3), round(float(s[:, 1].min()), 3), round(float(s[:, 1].max()), 3)))
    print('HP', label, out)
prof(M[M[:, 2] > 0.62], 'mm9')
prof(CO[headv & (CO[:, 2] > 0.62)], 'ours_all_head')
print('HP zmax mm9', round(float(M[:, 2].max()), 3), 'ours', round(float(CO[headv, 2].max()), 3))
