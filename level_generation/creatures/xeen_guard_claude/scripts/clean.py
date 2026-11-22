"""Clean the Smart Topology v1 return of Xeen's Guard -> work/clean_v1.blend (object Guard).
- import, apply transforms, scale to HEIGHT (dome top), ground (min z 0), centre x/y, forward -Y;
- delete needle triangles (aspect maxedge^2/2area > 10 with an edge over 6 cm, above the soles: Meshy's strips from
  the right hand to the right knee and from knee to knee) and the 3-7 vertex sliver pieces left by them;
- symmetrize +X -> -X (the creature's left half is clean; the right shin had holes and the right hand needles):
  the right hand, tube and sole are rebuilt as mirrors of the left ones; the red forearm band is paint;
- fill the remaining holes (boundary loops), recalculate normals outward, report pieces."""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.90
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
ob = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o, do_unlink=True)
ob.parent = None
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ob.name = ob.data.name = 'Guard'
ob.data.materials.clear()
co = np.array([v.co[:] for v in ob.data.vertices])
mn, mx = co.min(0), co.max(0)
k = HEIGHT / (mx[2] - mn[2])
off = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]))
for v in ob.data.vertices:
    v.co = (v.co - off) * k
bm = bmesh.new(); bm.from_mesh(ob.data)
bm.faces.ensure_lookup_table()
needles = []
for f in bm.faces:
    vs = [v.co for v in f.verts]
    e = max((vs[i] - vs[(i + 1) % len(vs)]).length for i in range(len(vs)))
    a = f.calc_area()
    if e > 0.06 and e * e / (2 * a + 1e-12) > 10 and f.calc_center_median().z > 0.1:
        needles.append(f)
print('NEEDLES', len(needles))
bmesh.ops.delete(bm, geom=needles, context='FACES')
# pieces; drop those under 12 vertices
bm.verts.ensure_lookup_table()
lab = [-1] * len(bm.verts); n = 0; sizes = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = n; c = 0
    while st:
        x = st.pop(); c += 1
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = n; st.append(w)
    sizes.append(c); n += 1
small = [v for v in bm.verts if sizes[lab[v.index]] < 12]
print('SLIVER verts', len(small))
bmesh.ops.delete(bm, geom=small, context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
# symmetrize: keep +X, mirror to -X
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='X', dist=1e-4)
bnd = [e for e in bm.edges if e.is_boundary]
print('BOUNDARY edges after symmetrize', len(bnd))
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
bmesh.ops.triangulate(bm, faces=res['faces'])
# chest rivets (small pieces off the midline that the mirror doubled): paint, not geometry
bm.verts.ensure_lookup_table()
lab = [-1] * len(bm.verts); groups = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = len(groups); g = []
    while st:
        x = st.pop(); g.append(x)
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = lab[v.index]; st.append(w)
    groups.append(g)
rivets = [v for g in groups if len(g) < 100 and 1.3 < g[0].co.z < 1.55 for v in g]
print('RIVET verts', len(rivets))
bmesh.ops.delete(bm, geom=rivets, context='VERTS')
# fins (the needle remnants at the inner knees): faces folded back onto a neighbour, deleted, holes refilled
for it in range(3):
    bm.normal_update()
    fins = set()
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < -0.6:
            fins.update(e.link_faces)
    print('FINS', it, len(fins))
    if not fins:
        break
    bmesh.ops.delete(bm, geom=list(fins), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=r['faces'])
# true spikes only (a vertex further from its neighbours' mean than 1.5 mean edges), above the soles
for it in range(3):
    moved = 0
    for v in bm.verts:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if len(nb) < 3 or v.co.z < 0.12: continue
        m = sum(nb, Vector()) / len(nb)
        el = sum((c - v.co).length for c in nb) / len(nb)
        if (v.co - m).length > 1.5 * el * 0.5 and (v.co - m).length > 0.02:
            v.co = m; moved += 1
    print('SPIKES moved', it, moved)
# holes that did not fill (bow-tie boundaries): open them by one ring of faces and fill again
for it in range(3):
    bv = {v for e in bm.edges if e.is_boundary for v in e.verts}
    if not bv:
        break
    ring = {f for v in bv for f in v.link_faces}
    bmesh.ops.delete(bm, geom=list(ring), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=r['faces'])
    print('REOPEN', it, len(bv), 'refilled', len(r['faces']))
print('FILLED faces', len(res['faces']), 'boundary left', sum(1 for e in bm.edges if e.is_boundary))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(ob.data); bm.free()
for p in ob.data.polygons:
    p.use_smooth = True
# report pieces
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lab = [-1] * len(bm.verts); rep = []
for v in bm.verts:
    if lab[v.index] >= 0: continue
    st = [v]; lab[v.index] = len(rep); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if lab[w.index] < 0: lab[w.index] = lab[v.index]; st.append(w)
    c = np.array([bm.verts[i].co[:] for i in idx])
    rep.append({'verts': len(idx), 'min': c.min(0).round(3).tolist(), 'max': c.max(0).round(3).tolist()})
rep.sort(key=lambda r: -r['verts'])
for i, r in enumerate(rep):
    print('PIECE', i, r['verts'], r['min'], r['max'])
print('TRIS', sum(len(f.verts) - 2 for f in bm.faces))
json.dump(rep, open(os.path.join(HERE, 'work', 'pieces_clean.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
me = bpy.data.objects['Guard'].data
np.save(os.path.join(HERE, 'work', 'clean_V.npy'), np.array([v.co[:] for v in me.vertices]))
me.calc_loop_triangles()
np.save(os.path.join(HERE, 'work', 'clean_F.npy'), np.array([t.vertices[:] for t in me.loop_triangles]))
