"""Step 1 cleanup of the m178 Smart Topology return (work/st_v1_parts.blend, loose parts P00..): every piece is kept
and joined into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (positions as uploaded to Meshy's
auto-rig, for the nearest-vertex weight transfer).
m178 repair on the skin (P00): three small holes (14 boundary edges: one on the right upper chest with folded
sliver triangles, one in the belly groove, one at the tail root). Merge coincident vertices, dissolve degenerate
faces, fill the boundary loops, make the winding consistent and outward. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
skin = P['P00']
bm = bmesh.new(); bm.from_mesh(skin.data)
nb0 = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
# folded slivers at the chest hole: faces whose edges are all boundary or non-manifold are removed before the fill
loose = [f for f in bm.faces if sum(1 for e in f.edges if e.is_boundary or not e.is_manifold) >= 2]
bmesh.ops.delete(bm, geom=loose, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=40)
# an edge shared by three faces (the chest fold) leaves a triangular hole the fill skips: remove every face
# around the fold and fill the larger hole
for _ in range(3):
    fan = [e for e in bm.edges if len(e.link_faces) > 2]
    if not fan:
        break
    ring = {f for e in fan for v in e.verts for f in v.link_faces}       # every face around the fold
    bmesh.ops.delete(bm, geom=list(ring), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=40)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
nb1 = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if not e.is_manifold)
bm.to_mesh(skin.data); bm.free()
print('CLEAN skin holes: boundary edges', nb0, '->', nb1, 'non-manifold', nm, 'removed sliver faces', len(loose))
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co), 'pieces', len(P))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
