"""v2 symmetry pass, step 2 (Blender): keep the +X half (left wing, legs and flank: the cleaner side; the right wing
had folded membrane and the longer leading finger), mirror it and weld on x = 0.

Applies straightened coordinates, then bmesh symmetrize (+X copied to -X, 0.4 mm weld; fewer open/non-manifold
midline edges than bisect + mirror), drops flat in-plane pieces and stray right-foot claws that crossed the plane,
removes degenerate faces, then relaxes a
12 mm band about the midline (Laplacian, symmetric, midline vertices keep x = 0) so the mirrored halves meet without a
crease. Usage: blender -b --python mirror_half.py -- <in.blend> <coords.npy> <out.blend> <report.json>"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; me = o.data
co = np.load(a[1]); assert len(co) == len(me.vertices)
me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
bm = bmesh.new(); bm.from_mesh(me)
before = sum(v.co.x >= 0 for v in bm.verts)
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='X', dist=4e-4)   # keeps +X
for v in bm.verts:
    if abs(v.co.x) < 1e-6: v.co.x = 0.
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-7)
# connected pieces: drop flat pieces lying in the plane and stray main-shell pieces straddling it (claws of the
# discarded right feet that crossed x = 0); crest shells (part > 0) are kept
part = bm.verts.layers.int['part']; bm.verts.ensure_lookup_table(); seen = set(); dropped = []; doomed = []
for v in list(bm.verts):
    if v.index in seen: continue
    stack = [v]; ids = []; seen.add(v.index)
    while stack:
        u = stack.pop(); ids.append(u)
        for e in u.link_edges:
            w = e.other_vert(u)
            if w.index not in seen: seen.add(w.index); stack.append(w)
    xs = [u.co.x for u in ids]
    flat = max(abs(t) for t in xs) < 1e-6
    stray = len(ids) < 1000 and min(xs) < 0 < max(xs) and all(u[part] == 0 for u in ids)
    if flat or stray:
        dropped.append({'vertices': len(ids), 'centre': [sum(u.co[k] for u in ids) / len(ids) for k in range(3)], 'flat': flat})
        doomed += ids
bmesh.ops.delete(bm, geom=doomed, context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free(); me.update()
# symmetric Laplacian relaxation of the midline band
co = np.array([v.co[:] for v in me.vertices]); nb = [[] for _ in co]
for e in me.edges:
    i, j = e.vertices; nb[i].append(j); nb[j].append(i)
band = np.abs(co[:, 0]) < .012; w = np.clip(1 - np.abs(co[:, 0]) / .012, 0, 1) * .5
onmid = co[:, 0] == 0
for _ in range(4):
    new = co.copy()
    for i in np.where(band)[0]:
        if not nb[i]: continue
        m = co[nb[i]].mean(0); new[i] = co[i] * (1 - w[i]) + m * w[i]
        if onmid[i]: new[i, 0] = 0.
    co = new
me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
# exact symmetry check
from mathutils import kdtree
kd = kdtree.KDTree(len(co))
for i, p in enumerate(co): kd.insert(p, i)
kd.balance(); dd = np.array([kd.find((-p[0], p[1], p[2]))[2] for p in co])
bm = bmesh.new(); bm.from_mesh(me)
rep = {'half_vertices_before_mirror': before, 'dropped_pieces': dropped, 'vertices': len(me.vertices), 'faces': len(me.polygons),
       'triangles': sum(len(f.vertices) - 2 for f in me.polygons), 'midline_vertices': int(onmid.sum()),
       'mirror_partner_distance_max_m': float(dd.max()), 'boundary_edges': sum(e.is_boundary for e in bm.edges),
       'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges)}
bm.free()
json.dump(rep, open(a[3], 'w'), indent=2); print('MIRROR', rep)
bpy.ops.wm.save_as_mainfile(filepath=a[2])
