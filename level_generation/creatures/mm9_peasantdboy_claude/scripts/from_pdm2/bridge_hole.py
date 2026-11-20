"""Close one see-through pinhole seen from the front (face pass 2026-11-02): the boundary vertices of 'Body' within R of the
view ray through (X, Z) (the ray runs along +y, Blender rest frame) are triangulated in the x-z plane and the triangles whose
projection contains a point within PAD of the ray (and are not already faces) are added, with the material, int attributes
and the centre UVs of the nearest old face (one texel per layer). No new vertices. Args: <in blend> <out blend> <x> <z> [R 0.008]"""
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt, intersect_point_tri_2d
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
X, Z = float(a[2]), float(a[3]); R = float(a[4]) if len(a) > 4 else 0.008
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm); OLD = list(bm.faces)
bv = [v for v in bm.verts if any(e.is_boundary for e in v.link_edges) and ((v.co.x - X) ** 2 + (v.co.z - Z) ** 2) ** 0.5 < R and v.co.y < -0.08]
print('BRIDGE boundary verts', len(bv))
vo, eo, fo, ov, oe, of = delaunay_2d_cdt([Vector((v.co.x, v.co.z)) for v in bv], [], [], 0, 1e-7, True)
uvl = [bm.loops.layers.uv[n] for n in bm.loops.layers.uv.keys()]; ints = list(bm.faces.layers.int.values())
added = 0
pts = [Vector((X + dx, Z + dz)) for dx in (-0.002, 0, 0.002) for dz in (-0.002, 0, 0.002)]
for f in fo:
    if not all(len(ov[k]) for k in f):
        continue
    vs = [bv[ov[k][0]] for k in f]
    t2 = [Vector((v.co.x, v.co.z)) for v in vs]
    if not any(intersect_point_tri_2d(p, *t2) for p in pts):
        continue
    if bm.faces.get(vs) is not None:
        continue
    if any(bm.edges.get((vs[i], vs[(i + 1) % 3])) is not None and not bm.edges.get((vs[i], vs[(i + 1) % 3])).is_boundary for i in range(3)):
        continue
    n = (vs[1].co - vs[0].co).cross(vs[2].co - vs[0].co)
    if n.y > 0:
        vs = [vs[0], vs[2], vs[1]]
    try:
        nf = bm.faces.new(vs)
    except ValueError:
        continue
    cen = sum((v.co for v in vs), Vector()) / 3
    src = OLD[bvh.find_nearest(cen)[2]]
    nf.material_index = src.material_index; nf.smooth = src.smooth
    for L in ints:
        nf[L] = src[L]
    for L in uvl:
        cu = sum((l[L].uv for l in src.loops), Vector((0, 0))) / len(src.loops)
        for l in nf.loops:
            l[L].uv = cu
    added += 1
bm.normal_update(); bm.to_mesh(me); me.update()
print('BRIDGE added', added)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
