"""Blender: the face-shell triangles of Meshy's pressed human ears (add_ears.py press=1): vertices of <v3 blend> that differ
from <M7 master>, their faces and one ring of neighbour faces; per corner HeadUV and a weight (1 on a moved vertex, 0 else).
Args: <v3 blend> <M7 master blend> <out npz>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[1])
P0 = np.array([v.co[:] for v in bpy.data.objects['Body'].data.vertices])
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
P = np.array([v.co[:] for v in me.vertices])[:len(P0)]
moved = np.zeros(len(me.vertices), bool); moved[:len(P0)] = np.linalg.norm(P - P0, axis=1) > 1e-6
ear = np.zeros(len(me.polygons), np.int32); me.attributes['ear'].data.foreach_get('value', ear)
faces = [p for p in me.polygons if not ear[p.index] and any(moved[v] for v in p.vertices)]
ring = {v for p in faces for v in p.vertices}
faces = [p for p in me.polygons if not ear[p.index] and any(v in ring for v in p.vertices)]
uv = me.uv_layers['HeadUV'].data
UV, W = [], []
for p in faces:
    l = list(p.loop_indices)
    for k in range(1, len(l) - 1):
        tri = [l[0], l[k], l[k + 1]]
        UV.append([uv[i].uv[:] for i in tri]); W.append([float(moved[me.loops[i].vertex_index]) for i in tri])
np.savez(a[2], UV=np.array(UV), W=np.array(W))
print('PRESS_DUMP moved', int(moved.sum()), 'triangles', len(UV))
# hair-shell triangles near the elf ear roots (the head views put the elf ear's base where Meshy's hair shell has its side
# edge, so Meshy painted skin onto the hair there): the second-largest head component, faces within 8 cm of either root
import bmesh
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen, comps = set(), []
for f in bm.faces:
    if f.index in seen or not hd[f.index] or hn[f.index] or ear[f.index]: continue
    st, c = [f], []; seen.add(f.index)
    while st:
        g = st.pop(); c.append(g.index)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen and hd[h.index] and not hn[h.index] and not ear[h.index]:
                    seen.add(h.index); st.append(h)
    comps.append(c)
comps.sort(key=len, reverse=True)
MID = -0.0111; ROOT = np.array([0.075, 0.004, 0.779])
roots = [np.array([MID + ROOT[0], ROOT[1], ROOT[2]]), np.array([MID - ROOT[0], ROOT[1], ROOT[2]])]
Pall = np.array([v.co[:] for v in me.vertices])
UVh, Dh = [], []
for fi in comps[1]:
    p = me.polygons[fi]
    cen = Pall[list(p.vertices)].mean(0)
    dist = min(np.linalg.norm(cen - r) for r in roots)
    if dist > 0.08:
        continue
    l = list(p.loop_indices)
    for k in range(1, len(l) - 1):
        tri = [l[0], l[k], l[k + 1]]
        UVh.append([uv[i].uv[:] for i in tri]); Dh.append([min(np.linalg.norm(Pall[me.loops[i].vertex_index] - r) for r in roots) for i in tri])
np.savez(a[2].replace('.npz', '_hair.npz'), UV=np.array(UVh), D=np.array(Dh))
print('HAIR_DUMP triangles', len(UVh))
# neck: face-shell (largest head component) triangles with any corner below z 0.73 (the head views' high brocade collar was
# painted onto the neck skin; the body's collar sits lower): per corner HeadUV and z
UVn, Zn = [], []
for fi in comps[0]:
    p = me.polygons[fi]
    zs = [Pall[v][2] for v in p.vertices]
    if min(zs) > 0.73:
        continue
    l = list(p.loop_indices)
    for k in range(1, len(l) - 1):
        tri = [l[0], l[k], l[k + 1]]
        UVn.append([uv[i].uv[:] for i in tri]); Zn.append([Pall[me.loops[i].vertex_index][2] for i in tri])
np.savez(a[2].replace('.npz', '_neck.npz'), UV=np.array(UVn), Z=np.array(Zn))
print('NECK_DUMP triangles', len(UVn))
