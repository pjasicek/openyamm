"""Close the see-through gap in the right cheek (Meshy left the beard sheet's open boundary short of the face shell there:
the background showed through beside the nose). Boundary vertices of 'Body' within R of the given point are projected
onto the plane facing the view direction D, Delaunay-triangulated, and the triangles that cover empty space (a ray along
-D from the centroid hits nothing within 2 cm), with edges under EMAX, are added as faces. New faces copy the material
and the int attributes (head, hand) of the nearest old face and collapse every UV layer to that face's centre UV (one
texel colour, no stretch), as build_export_v2.py's hole fill. No new vertices: weights unchanged.
Args: <in blend> <out blend> <x,y,z> [R 0.025] [EMAX 0.02] [dx,dy,dz view direction toward the camera, default 0,-1,0]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
C = Vector([float(t) for t in a[2].split(',')]); R = float(a[3]) if len(a) > 3 else 0.025
EMAX = float(a[4]) if len(a) > 4 else 0.02
D = Vector([float(t) for t in a[5].split(',')]).normalized() if len(a) > 5 else Vector((0, -1, 0))
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
bv = [v for v in bm.verts if (v.co - C).length < R and any(e.is_boundary for e in v.link_edges)]
print('BOUNDARY_VERTS', len(bv))
u = D.orthogonal().normalized(); w = D.cross(u)
P2 = np.array([[v.co.dot(u), v.co.dot(w)] for v in bv])
_vo, _eo, _fo, _ov, _oe, _of = delaunay_2d_cdt([Vector(p) for p in P2], [], [], 0, 1e-6, True)
simp = [[_ov[k][0] for k in f] for f in _fo if all(len(_ov[k]) for k in f)]
uvl = [bm.loops.layers.uv[n] for n in bm.loops.layers.uv.keys()]
ints = list(bm.faces.layers.int.values())
added = 0
OLD = list(bm.faces)
OLDSET = set(OLD)
smooth_uv = 0
UVR = 0.03
for s in simp:
    vs = [bv[i] for i in s]
    if max((vs[i].co - vs[(i + 1) % 3].co).length for i in range(3)) > EMAX:
        continue
    if bm.faces.get(vs) is not None:
        continue
    cen = (vs[0].co + vs[1].co + vs[2].co) / 3
    # empty space: no surface just in front of / behind the centroid along the view axis
    h1 = bvh.ray_cast(cen + D * 0.02, -D, 0.04)
    if h1[0] is not None and (h1[0] - cen).length < 0.004:
        continue
    # an edge may only be used if it is new or a boundary edge (keeps the patch manifold)
    ok = True
    for i in range(3):
        e = bm.edges.get((vs[i], vs[(i + 1) % 3]))
        if e is not None and not e.is_boundary:
            ok = False
    if not ok:
        continue
    _, _, fi, _ = bvh.find_nearest(cen)
    src = OLD[fi]
    # wind like the neighbour: new normal toward the camera side
    n = (vs[1].co - vs[0].co).cross(vs[2].co - vs[0].co)
    if n.dot(D) < 0:
        vs = [vs[0], vs[2], vs[1]]
    try:
        f = bm.faces.new(vs)
    except ValueError:
        continue
    f.material_index = src.material_index; f.smooth = src.smooth
    for L in ints:
        f[L] = src[L]
    for L in uvl:
        cu = sum((l[L].uv for l in src.loops), Vector((0, 0))) / len(src.loops)
        # each vertex's own UV from its old loop nearest the source face's centre UV; used when all three lie near
        # the source island (smooth paint across the patch), else one texel for the whole face (no smear across seams)
        pick = []
        for l in f.loops:
            cands = [ol[L].uv.copy() for ol in l.vert.link_loops if ol.face is not f and ol.face in OLDSET]
            pick.append(min(cands, key=lambda q: (q - cu).length) if cands else None)
        if all(q is not None and (q - cu).length < UVR for q in pick):
            for l, q in zip(f.loops, pick):
                l[L].uv = q
            smooth_uv += 1
        else:
            for l in f.loops:
                l[L].uv = cu
    added += 1
bm.normal_update()
bm.to_mesh(me); me.update()
print('PATCHED faces', added, 'smooth-uv layer faces', smooth_uv)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
