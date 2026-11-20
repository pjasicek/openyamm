"""Hood/hair extents of a design master vs its MM9 model (diagnosis): per height band, the half-width |x| max and the back
depth y max of our hair part and of MM9's head-weighted surface (shifted by the fit's Head move). Args: <blend> <mm9 glb> <fit json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; M = body.matrix_world
move = Vector([x / 100.0 for x in json.load(open(a[2]))['joint_moves_xyz_cm']['Bip01 Head']])
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
comp = {}; parts = []
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = len(parts); cur = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = len(parts); st.append(o); cur.append(o)
    parts.append(cur)
big = max(range(len(parts)), key=lambda i: len(parts[i]))
cand = [i for i in range(len(parts)) if i != big and len(parts[i]) > 200 and np.mean([(M @ v.co).z for v in parts[i]]) > 0.38]
hair = np.array([tuple(M @ v.co) for v in parts[max(cand, key=lambda i: len(parts[i]))]])
ex = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=a[1])
mm = max((o for o in bpy.data.objects if o not in ex and o.type == 'MESH'), key=lambda o: len(o.data.vertices))
KEEP = ('Bip01 Head', 'Bip01 Ponytail1', 'LF_tail', 'LF_tail2', 'LF_tail3', 'RF_tail', 'RF_tail2', 'RF_tail3')
gi = {g.index for g in mm.vertex_groups if g.name in KEEP}
P = np.array([tuple(mm.matrix_world @ v.co + move) for v in mm.data.vertices if sum(g.weight for g in v.groups if g.group in gi) > 0.5])
for z in (0.50, 0.46, 0.42, 0.38, 0.34, 0.30):
    h = hair[np.abs(hair[:, 2] - z) < 0.015]; m = P[np.abs(P[:, 2] - z) < 0.02]
    f = lambda q: (round(float(np.abs(q[:, 0]).max()), 3), round(float(q[:, 1].max()), 3)) if len(q) else None
    print('BAND', z, 'ours |x|,ymax', f(h), 'mm9', f(m))
print('TOP ours', round(float(hair[:, 2].max()), 3), 'mm9', round(float(P[:, 2].max()), 3))
