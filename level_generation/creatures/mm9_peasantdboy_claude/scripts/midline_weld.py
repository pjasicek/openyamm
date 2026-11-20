"""Weld the mirror midline (generalised bridge_weld.py): sym_meshy.py / sym_rigged.py leave vertex pairs under 1 mm apart
on x = 0, unwelded, with needle triangles between them; their normals shade as dark 'X' pinches on the forehead, hair crown
and chin in clay and viewer light. Every vertex with |x| < XW is welded within DIST (remove_doubles: each pair becomes one
vertex, faces keep their own UV loops), zero-area faces there are dissolved, n-gons triangulated, midline x snapped to 0.
Positions/faces only (UVs of the remaining faces unchanged; collapsed faces had zero UV area). Args: <in> <out> [xw 0.0015] [dist 0.001]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
XW = float(a[2]) if len(a) > 2 else 0.0015
DIST = float(a[3]) if len(a) > 3 else 0.001
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
vs = [v for v in bm.verts if abs(v.co.x) < XW]
n0, f0 = len(bm.verts), len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=vs, dist=DIST)
fz = [f for f in bm.faces if f.calc_area() < 1e-9 and any(abs(v.co.x) < 0.004 for v in f.verts)]
ez = list({e for f in fz for e in f.edges})
if ez:
    bmesh.ops.dissolve_degenerate(bm, dist=0.0002, edges=ez)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-12], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for v in bm.verts:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0.0
print('MIDWELD', {'zone_verts': len(vs), 'welded': n0 - len(bm.verts), 'faces_removed': f0 - len(bm.faces), 'zero_faces': len(fz)})
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
