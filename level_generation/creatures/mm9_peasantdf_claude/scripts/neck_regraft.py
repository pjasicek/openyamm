"""Head/body texture seam moved up under the jaw (user review r6, 2026-11-02: "head graft obviously wrong since it cuts off
the pendant?": the head set's lower edge was a level band across the base of the neck and the top of the chest, and the
body paint's necklace chain stopped under it). The one-shell body is cut level again at Z (default 0.338 m, just under
the jaw and the chin's underside, in the MM9 frame) and every face of the big shell that lies wholly below it within
R of the neck axis goes back to the body material (`head` = 0): those faces always had body UVs (texpass_uv.py kept them
in the body atlas, painted by the body retexture), so the neck below the jaw, the collar line and the necklace now come
from the body paint. The hair/hood part and the hands keep their sets. Positions on the surface unchanged (the cut only
adds vertices on existing edges; UVs interpolate). Args (Blender): <in blend> <out blend> [Z 0.338] [R 0.16]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z = float(a[2]) if len(a) > 2 else 0.338
R = float(a[3]) if len(a) > 3 else 0.16
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
nc = rig.matrix_world @ rig.data.bones['Bip01 Neck'].head_local
M = ob.matrix_world; Mi = M.inverted()
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
lk = bm.faces.layers.int['head']; lh = bm.faces.layers.int['hand']; lt = bm.faces.layers.int.get('twin')
comp = {}; k = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = k; st.append(o)
    k += 1
big = int(np.bincount(list(comp.values())).argmax())
near = lambda w: (Vector((w.x, w.y)) - Vector((nc.x, nc.y))).length < R
geom = [f for f in bm.faces if comp[f.verts[0]] == big and f[lk] and not f[lh]
        and all(abs((M @ v.co).z - Z) < 0.03 and near(M @ v.co) for v in f.verts)]
edges = {e for f in geom for e in f.edges}; verts = {v for f in geom for v in f.verts}
co = Mi @ Vector((0, 0, Z)); no = (Mi.to_3x3().transposed().inverted() @ Vector((0, 0, 1))).normalized()
bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + geom, plane_co=co, plane_no=no)
nf = [f for f in bm.faces if len(f.verts) > 3]
bmesh.ops.triangulate(bm, faces=nf)
bm.faces.ensure_lookup_table()
comp = {}; k = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = k; st.append(o)
    k += 1
big = int(np.bincount(list(comp.values())).argmax())
moved = 0
for f in bm.faces:
    if comp[f.verts[0]] == big and f[lk] and not f[lh] and not (lt and f[lt]):
        ws = [M @ v.co for v in f.verts]
        if max(w.z for w in ws) <= Z + 1e-5 and all(near(w) for w in ws):
            f[lk] = 0; moved += 1
bm.to_mesh(ob.data); ob.data.update()
print('REGRAFT', json.dumps({'cut_z': Z, 'faces_to_body': moved, 'tris': sum(len(p.vertices) - 2 for p in ob.data.polygons)}))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
