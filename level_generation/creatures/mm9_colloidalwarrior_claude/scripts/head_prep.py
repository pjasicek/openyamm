"""(colloidal warrior, from mm9_bigfoot_claude) Head-only Meshy return -> clean symmetric head parts. Voxel remesh of the shell closes the torn shards round the mouth and nose; left half (x > 0) mirrored; teeth, eyes and horns from their own pieces.
Objects written: Face (skin + mane + ears shell), Horns, Eyes, Teeth, in the Meshy normalised frame, Blender axes. Args: <meshy glb> <out blend> [voxel] [face tris]"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = a[0], a[1]
RELAX = int(a[2]) if len(a) > 2 else 6
SIDE = -1.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True)
groups = {'Face': [], 'Eyes': []}
for i, cc in enumerate(comps):
    q = np.array([v.co[:] for v in cc]); c = q.mean(0); e = np.ptp(q, 0)
    if i == 0: g = 'Face'
    elif len(cc) > 100 and c[2] > 0.09 and abs(c[0]) > 0.05: g = 'Eyes'     # the two slit-eye pieces
    else: g = None          # lower-lid scraps and the bead teeth: the grin is painted on the closed lips
    print('COMP', i, len(cc), np.round(c, 3).tolist(), np.round(e, 3).tolist(), g)
    if g: groups[g].append(cc)
def make(name, comps_):
    ids = {v for cc in comps_ for v in cc}
    t = bm.copy(); t.verts.ensure_lookup_table()
    drop = [v for v in t.verts if bm.verts[v.index] not in ids] if False else None
    return ids
bm.verts.ensure_lookup_table(); bm.verts.index_update()
objs = {}
for name, cl in groups.items():
    keep = {v.index for cc in cl for v in cc}
    t = bm.copy(); t.verts.ensure_lookup_table()
    bmesh.ops.delete(t, geom=[v for v in t.verts if v.index not in keep], context='VERTS')
    m = bpy.data.meshes.new(name); t.to_mesh(m); t.free()
    ob = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(ob); objs[name] = ob
bm.free(); bpy.data.objects.remove(o)
def apply_mod(ob, m):
    bpy.context.view_layer.objects.active = ob
    for x in bpy.data.objects: x.select_set(x is ob)
    bpy.ops.object.modifier_apply(modifier=m.name)
# Face: small tears filled, left half mirrored, folds relaxed
f = objs['Face']
bm = bmesh.new(); bm.from_mesh(f.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
ORIG = set(bm.faces)
def cycles():
    """boundary edges split into simple cycles: a tear pinched at a vertex is its own hole"""
    bd = {e for e in bm.edges if e.is_boundary}
    out = []
    while bd:
        e0 = next(iter(bd)); path = [e0.verts[0]]; used = []
        cur = e0.verts[0]
        while True:
            nxt = next((e for e in cur.link_edges if e in bd and e not in used), None)
            if nxt is None: 
                for e in used: bd.discard(e)
                break
            used.append(nxt); cur = nxt.other_vert(cur)
            if cur in path:
                i = path.index(cur); cyc = used[i:]; out.append(cyc)
                for e in cyc: bd.discard(e)
                used = used[:i]; path = path[:i + 1]
                if not used:
                    break
                cur = path[-1]
            else:
                path.append(cur)
    return out
for rnd in range(3):
    cyc = cycles()
    print('LOOPS', len(cyc), sorted((len(c) for c in cyc), reverse=True)[:24])
    n = 0
    for c in cyc:
        q = np.array([v.co[:] for e in c for v in e.verts])
        if rnd == 0: print('LOOP', len(c), np.round(q.mean(0), 3).tolist(), np.round(np.ptp(q, 0), 3).tolist())
        mouth = len(c) > 20 and q[:, 2].mean() < 0.09
        sock = len(c) > 20 and not mouth
        if mouth or sock:      # a groove behind the lips, a floor behind the eye: extruded back, then capped, so the shell is closed for the wrap
            ext = bmesh.ops.extrude_edge_only(bm, edges=c)
            nv = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]; ne = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
            cen = sum((v.co for v in nv), Vector()) / len(nv)
            for v in nv:
                v.co = cen + (v.co - cen) * Vector((0.96, 1, 0.5 if mouth else 0.8)) + Vector((0, 0.05, 0))
            bmesh.ops.holes_fill(bm, edges=ne, sides=len(ne))
            print('CAP', 'mouth' if mouth else 'socket', len(c)); n += 1
        else:
            bmesh.ops.contextual_create(bm, geom=c) if len(c) < 5 else bmesh.ops.holes_fill(bm, edges=c, sides=len(c))
            n += 1
    print('FILLED', n)
bmesh.ops.triangulate(bm, faces=[g for g in bm.faces if len(g.verts) > 4])
bm.normal_update()
new_ = [g for g in bm.faces if g not in ORIG]
for it in range(4):
    flip = []
    for g in new_:
        s_ = Vector()
        for v in g.verts:
            for h in v.link_faces:
                if h in ORIG: s_ += h.normal * h.calc_area()
        if g.normal.dot(s_) < 0: flip.append(g)
    print('FLIP', it, len(flip), 'of', len(new_))
    if not flip: break
    bmesh.ops.reverse_faces(bm, faces=flip); bm.normal_update()
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(SIDE, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
r_ = bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.reverse_faces(bm, faces=[g for g in bm.faces if g.calc_center_median().x < 0])
# folds: vertices on edges bent past 55 degrees relax, except the open rims
for it in range(RELAX):
    bm.normal_update()
    w = {}
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > 0.95:
            for v in e.verts: w[v] = 1
    mv = {}
    for v in w:
        if v.is_boundary or abs(v.co.y) > 9: continue
        if v.co.y < -0.25:      # the face
            nb = [e.other_vert(v).co for e in v.link_edges]
            mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items():
        k = 0.0 if abs(v.co.x) > 1e-5 else 0.0
        v.co = v.co * 0.4 + c * 0.6
        if abs(c.x) < 1e-4 and abs(v.co.x) < 2e-3: v.co.x = 0
    print('RELAX', it, len(mv))
bm.to_mesh(f.data); bm.free()
print('FACE tris raw', sum(len(p.vertices) - 2 for p in f.data.polygons))
# paired pieces: x > 0 kept and mirrored; a piece across the centre stays and is symmetrised by nothing (teeth are small)
for name in ('Eyes',):
    ob = objs[name]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    seen = set(); comps = []
    for v in bm.verts:
        if v in seen: continue
        st = [v]; seen.add(v); cc = [v]
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y); cc.append(y)
        comps.append(cc)
    drop = []; keep = []
    for cc in comps:
        q = np.array([v.co[:] for v in cc]); cx = q[:, 0].mean()
        if abs(cx) < 0.012: continue          # central piece
        (keep if cx * SIDE > 0 else drop).extend(cc)
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    r = bmesh.ops.duplicate(bm, geom=[v for v in keep if v.is_valid] + list({e for v in keep for e in v.link_edges}) + list({f_ for v in keep for f_ in v.link_faces}))
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    for v in nv: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=[g for g in r['geom'] if isinstance(g, bmesh.types.BMFace)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    print('PIECES', name, len(comps), 'verts', len(ob.data.vertices))
for ob in objs.values():
    for p in ob.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADPREP', OUT)
