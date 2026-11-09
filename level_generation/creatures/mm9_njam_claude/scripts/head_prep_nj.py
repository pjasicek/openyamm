"""Njam (from mm9_nobleman_claude/scripts/head_prep_nb.py): Meshy returned the face shell, a separate hair helmet, eyeballs, and loose
brows, lid strips and a lip strip. Brows, lids and lip go (paint); Face, Hair and Eyes stay. Eyes found by position, yaw from the eye
line sorted by x.
Head-only Meshy model -> objects Face, Hair and Eyes, in metres, head-local (crown at z = 0.15), symmetric. Meshy fused hair and face into one closed shell, so there is no separate hair part;
the teeth pieces go (no jaw bone in MM9). The figure's right half is kept (the left has a tear at the nape) and mirrored, the face stays denser than the hair. Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.30
TRIS = {'Face': 100000, 'Hair': 100000, 'Eyes': 100000}   # full resolution: head_fix_nj.py resamples face and hair
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
o.parent = None; o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices])
n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
order = np.argsort(-np.bincount(comp))
print('COMPS', [int((comp == c).sum()) for c in order])
sizes = np.bincount(comp)
cand = [c for c in order[2:8] if sizes[c] > 250]           # the two eyeballs: the next pieces after face and hair
eyes_c = sorted(cand[:2], key=lambda c: P[comp == c][:, 0].mean())
e2, e1 = P[comp == eyes_c[0]].mean(0), P[comp == eyes_c[1]].mean(0)   # e1 = +x eye
print('EYES', e1.round(3), e2.round(3))
c = 0.5 * (e1 + e2)
R = np.arctan2(e1[1] - e2[1], e1[0] - e2[0])     # yaw of the eye line
ca, sa = np.cos(-R), np.sin(-R)
Q = P - np.array([c[0], 0, 0.5])
Q = np.c_[Q[:, 0] * ca - Q[:, 1] * sa, Q[:, 0] * sa + Q[:, 1] * ca, Q[:, 2]]
Q[:, 1] -= 0.0 * 0
print('YAW deg', round(float(np.degrees(R)), 2))
for v, p in zip(me.vertices, Q * S): v.co = Vector(p + np.array([0, 0, 0.15]))
ids = {'Face': [order[0]], 'Hair': [order[1]], 'Eyes': eyes_c}
for k, cs in ids.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
def fill_small(bm, limit):
    for _ in range(3):
        seen = set(); comps = []
        for e in [e for e in bm.edges if e.is_boundary]:
            if e in seen: continue
            st = [e]; seen.add(e); cur = []
            while st:
                x = st.pop(); cur.append(x)
                for v in x.verts:
                    for y in v.link_edges:
                        if y.is_boundary and y not in seen: seen.add(y); st.append(y)
            comps.append(cur)
        for cur in comps:
            if len(cur) <= limit: bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
for ob in bpy.data.objects:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for e in bm.edges:                                       # Meshy's shell is closed: every boundary edge of the half is the seam
        if e.is_boundary:
            for v in e.verts:
                if abs(v.co.x) < 0.004: v.co.x = 0
    bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
    fill_small(bm, 40)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    print('OBJ', ob.name, 'full', len(bm.faces), 'boundary', sum(1 for e in bm.edges if e.is_boundary))
    bm.to_mesh(ob.data); bm.free()
    if ob.name == 'Hair':                                    # Meshy's lumps on the hair helmet: light relax, rims kept
        bm = bmesh.new(); bm.from_mesh(ob.data)
        hv = [v for v in bm.verts if not any(e.is_boundary for e in v.link_edges)]
        for it in range(4):
            mv = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in hv if abs(v.co.x) > 1e-6}
            for v, c in mv.items(): v.co = v.co * 0.6 + c * 0.4
        bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.objects.active = ob
    for x in bpy.data.objects: x.select_set(x is ob)
    d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, TRIS[ob.name] / len(ob.data.polygons)); d.use_symmetry = True; d.symmetry_axis = 'X'; d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='D')
    bm = bmesh.new(); bm.from_mesh(ob.data); fill_small(bm, 40); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    seen = set(); comps = []
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st = [e]; seen.add(e); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        comps.append(cur)
    for c_ in comps:                                        # temple and seam pin holes close to a point; the mouth (no jaw, no teeth) closes flat; the rings under the hair stay
        vs_ = list({v for e in c_ for v in e.verts})
        q = np.array([v.co[:] for v in vs_])
        if len(c_) <= 10: bmesh.ops.pointmerge(bm, verts=vs_, merge_co=Vector(q.mean(0)))
        elif q[:, 2].max() < -0.05 and q[:, 2].min() > -0.1 and q[:, 1].max() < -0.05: bmesh.ops.holes_fill(bm, edges=c_, sides=len(c_))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    print('OBJ rings', [(len(c_), [round(float(q), 3) for q in np.min([v.co[:] for e in c_ for v in e.verts], 0)], [round(float(q), 3) for q in np.max([v.co[:] for e in c_ for v in e.verts], 0)]) for c_ in comps if c_ and c_[0].is_valid and len(c_) > 10])
    print('OBJ', ob.name, 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2))
    bm.to_mesh(ob.data); bm.free()
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    print('OBJ', ob.name, len(ob.data.vertices), len(ob.data.polygons), np.round(np.min([v.co[:] for v in ob.data.vertices], 0), 3), np.round(np.max([v.co[:] for v in ob.data.vertices], 0), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
