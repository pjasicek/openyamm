"""Exact left-right symmetry of the weighted, reduced 'Body' (the decimation of the symmetric Meshy mesh is not
symmetric): the +X half is kept and mirrored onto -X, welded on the midline, its weights moved to the matching
L/R bones (midline vertices take the mean of both). No holes are filled (cloth rims stay open). Args: <in> <out blend>"""
import bpy, bmesh, sys
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
names = [g.name for g in body.vertex_groups]
idx = {n: i for i, n in enumerate(names)}
# Krohn: side bones without an L/R token (cape, hair, skirt flap pivots) swap by explicit pairs
PAIRS = {'Zcapepiv01': 'Zcapepiv02', 'Zcape01': 'Zcapepiv02', 'Ybackpiv01': 'Ybackpiv02', 'YfrontA01': 'YfrontA02',
         'Xhairpiv01': 'Xhairpiv02', 'XhairA01': 'XhairA02', 'XhairB01': 'XhairB02', 'XhairC01': 'XhairC02'}
PAIRS.update({v: k for k, v in list(PAIRS.items()) if k != 'Zcape01'})
def swap(n):
    if n in PAIRS:
        return PAIRS[n]
    return n.replace(' L ', ' @ ').replace(' R ', ' L ').replace(' @ ', ' R ')
for n in names:
    if swap(n) not in idx:
        body.vertex_groups.new(name=swap(n)); idx[swap(n)] = len(idx)
names = [g.name for g in body.vertex_groups]
sw = {i: idx[swap(n)] for i, n in enumerate(names)}
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active
n0 = len(bm.verts)
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0),
                       plane_no=(-1, 0, 0), clear_outer=True, dist=1e-6)
for v in bm.verts:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0
bf = set(bm.faces)
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-5)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f not in bf])
nw = 0
for v in bm.verts:
    d = v[dl]
    w = dict(d.items())
    if v.co.x < -1e-6:
        d.clear()
        for k, a in w.items():
            d[sw[k]] = a
        nw += 1
    elif abs(v.co.x) <= 1e-6:
        d.clear(); out = {}
        for k, a in w.items():
            out[k] = out.get(k, 0) + a / 2; out[sw[k]] = out.get(sw[k], 0) + a / 2
        for k, a in out.items():
            d[k] = a
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('SYMR verts', n0, '->', len(bm.verts), 'tris', len(bm.faces), 'mirrored', nw,
      'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold))
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
